import re

from app.ai.domain.entities import (
    AIExecutionContext,
    AIRequest,
    PlannedQuery,
    QueryResult,
)
from app.ai.domain.interfaces import AIProvider, PromptTemplate, SchemaProvider


class QueryPlanner:
    def __init__(
        self,
        schema_provider: SchemaProvider,
        prompt_template: PromptTemplate,
        ai_provider: AIProvider,
    ) -> None:
        self._schema_provider = schema_provider
        self._prompt_template = prompt_template
        self._ai_provider = ai_provider

    async def plan_query(
        self, question: str, context: AIExecutionContext
    ) -> PlannedQuery:

        print("=" * 80)
        print("INICIO plan_query()")
        print("=" * 80)

        schema = await self._schema_provider.get_database_schema()
        context.database_schema = schema

        import re
        import unicodedata

        def normalize(text: str) -> str:
            nfkd = unicodedata.normalize('NFKD', text)
            no_accents = "".join([c for c in nfkd if not unicodedata.combining(c)])
            return re.sub(r'[^\w\s]', '', no_accents.lower()).strip()

        clean_q = normalize(question)
        greetings = {
            "hola", "buenas", "buenos dias", "buenas tardes", "buenas noches",
            "saludos", "hi", "hello", "que tal", "como estas", "quien eres",
            "hola buenas", "hola que tal", "hola como estas"
        }

        is_simple_greeting = clean_q in greetings or any(clean_q.startswith(g + " ") for g in {"hola", "buenas", "saludos", "hi", "hello"})
        is_query_intent = any(w in clean_q for w in ["mascota", "usuario", "adopcion", "rol", "permiso", "cuanto", "cuanta", "cuantos", "cuantas", "lista", "busca", "mostrar", "muestrame", "ver", "registrad", "id", "tabla"])

        if is_simple_greeting and not is_query_intent and len(clean_q.split()) <= 4:
            sql = "SELECT 'greeting' AS type"
            print("Detectado saludo -> Usando consulta directa de bienvenida")
            return PlannedQuery(
                sql=sql,
                schema=schema,
                prompt="Greeting detection",
            )

        print("Generando prompt para consulta de datos...")
        prompt = self._prompt_template.render_sql_prompt(
            question=question,
            schema=schema,
            context=context,
        )

        ai_response = await self._ai_provider.generate(
            AIRequest(prompt=prompt)
        )

        sql = self._extract_sql(ai_response.content)

        if not sql:
            sql = "SELECT 'greeting' AS type"

        return PlannedQuery(
            sql=sql,
            schema=schema,
            prompt=prompt,
        )

    async def format_response(
        self,
        question: str,
        sql: str,
        result: QueryResult,
        context: AIExecutionContext,
    ) -> str:

        if "SELECT 'greeting' AS type" in sql:
            return (
                "¡Hola! Soy tu asistente SQL de PetHouse. 🐾\n"
                "¿En qué te puedo ayudar hoy? Puedo consultar información sobre mascotas, "
                "usuarios, solicitudes de adopción o registros del sistema."
            )

        prompt = self._prompt_template.render_response_prompt(
            question=question,
            sql=sql,
            result=result,
            context=context,
        )

        ai_response = await self._ai_provider.generate(
            AIRequest(prompt=prompt)
        )

        cleaned_response = re.sub(r"(?s)<think>.*?</think>", "", ai_response.content).strip()
        return cleaned_response

    def _extract_sql(self, content: str) -> str:
        cleaned = content.strip()

        # 1. Eliminar etiquetas <think>...</think>
        cleaned = re.sub(r"(?s)<think>.*?</think>", "", cleaned).strip()

        # 2. Si el SQL está en un bloque de código Markdown ```sql ... ```
        code_block_match = re.search(r"```(?:sql)?\s*(.*?)\s*```", cleaned, re.DOTALL | re.IGNORECASE)
        if code_block_match:
            cleaned = code_block_match.group(1).strip()

        # 3. Eliminar etiquetas XML específicas de envoltorio (<sql>, </sql>, <query>, </query>)
        cleaned = re.sub(r"</?(?:sql|query)>", "", cleaned, flags=re.IGNORECASE).strip()

        # 4. Extraer desde el primer SELECT o WITH hasta el primer punto y coma ';' (o fin de instrucción)
        match = re.search(r"(?is)\b(SELECT|WITH)\b.*?(?:;|$)", cleaned)
        if match:
            cleaned = match.group(0).strip()

        # 5. Limpieza final de punto y coma final, comillas simples o backticks sobrantes
        cleaned = cleaned.rstrip(";` \t\r\n")

        print("=" * 80)
        print("SQL DESPUÉS DE LIMPIEZA")
        print("=" * 80)
        print(cleaned)
        print("=" * 80)

        return cleaned.strip()