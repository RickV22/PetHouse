import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.controllers.pet_controller import create_pet
from app.schemas.pet_schema import PetCreate


class FakeQuery:
    def __init__(self, result):
        self.result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.result


class FakeDB:
    def __init__(self, user):
        self.user = user
        self.added = []

    def query(self, model):
        if model.__name__ == "User":
            return FakeQuery(self.user)
        return FakeQuery(None)

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        return None

    def refresh(self, obj):
        setattr(obj, "id", 1)


def test_create_pet_sends_submission_email_for_pending_review(monkeypatch):
    calls = []

    def fake_send_email(user_email, user_name, pet_name):
        calls.append((user_email, user_name, pet_name))
        return True

    monkeypatch.setattr("app.controllers.pet_controller.send_pet_submission_email", fake_send_email, raising=False)
    monkeypatch.setattr("app.controllers.pet_controller.log_action", lambda **kwargs: None)

    user = types.SimpleNamespace(id=1, role_id=2, email="user@example.com", name="Ana", last_name=None)
    db = FakeDB(user)
    pet_data = PetCreate(
        name="Luna",
        species="Perro",
        race="Mestizo",
        birth_date=None,
        gender="Hembra",
        description="Mascota muy cariñosa",
        image_url=None,
        modalidad="sede",
        telefono_contacto="3001234567",
    )

    created_pet = create_pet(db, pet_data, user_id=1, image=None)

    assert created_pet.name == "Luna"
    assert calls == [("user@example.com", "Ana", "Luna")]
