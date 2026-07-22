
// this file is generated — do not edit it


declare module "svelte/elements" {
	export interface HTMLAttributes<T> {
		'data-sveltekit-keepfocus'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-noscroll'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-preload-code'?:
			| true
			| ''
			| 'eager'
			| 'viewport'
			| 'hover'
			| 'tap'
			| 'off'
			| undefined
			| null;
		'data-sveltekit-preload-data'?: true | '' | 'hover' | 'tap' | 'off' | undefined | null;
		'data-sveltekit-reload'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-replacestate'?: true | '' | 'off' | undefined | null;
	}
}

export {};


declare module "$app/types" {
	export interface AppTypes {
		RouteId(): "/" | "/admin" | "/admin/adopcion" | "/admin/dashboard" | "/admin/historial" | "/admin/mascotas" | "/auth" | "/auth/google" | "/auth/google/callback" | "/login" | "/usuarios" | "/usuarios/adoptar" | "/usuarios/mascotas" | "/usuarios/publicar" | "/usuarios/rastreador";
		RouteParams(): {
			
		};
		LayoutParams(): {
			"/": Record<string, never>;
			"/admin": Record<string, never>;
			"/admin/adopcion": Record<string, never>;
			"/admin/dashboard": Record<string, never>;
			"/admin/historial": Record<string, never>;
			"/admin/mascotas": Record<string, never>;
			"/auth": Record<string, never>;
			"/auth/google": Record<string, never>;
			"/auth/google/callback": Record<string, never>;
			"/login": Record<string, never>;
			"/usuarios": Record<string, never>;
			"/usuarios/adoptar": Record<string, never>;
			"/usuarios/mascotas": Record<string, never>;
			"/usuarios/publicar": Record<string, never>;
			"/usuarios/rastreador": Record<string, never>
		};
		Pathname(): "/" | "/admin" | "/admin/adopcion" | "/admin/dashboard" | "/admin/historial" | "/admin/mascotas" | "/auth/google/callback" | "/login" | "/usuarios" | "/usuarios/adoptar" | "/usuarios/mascotas" | "/usuarios/publicar" | "/usuarios/rastreador";
		ResolvedPathname(): `${"" | `/${string}`}${ReturnType<AppTypes['Pathname']>}`;
		Asset(): "/img/hero_pets_cartoon.png" | "/img/paw_icon.png" | "/robots.txt" | string & {};
	}
}