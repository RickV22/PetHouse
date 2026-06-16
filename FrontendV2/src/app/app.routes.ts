import { Routes } from '@angular/router';
import { HomeComponent } from './features/main/pages/home/home.component';
import { PublicarComponent } from './features/main/pages/publicar/publicar.component';
import { AdoptarComponent } from './features/main/pages/adoptar/adoptar.component';
import { authGuard } from './core/guards/auth.guard';
import { LoginComponent } from './features/login/pages/login/login.component';
import { MascotasComponent } from './features/main/pages/mascotas/mascotas.component';
import { adminGuard } from './core/guards/admin.guard';
import { AdminUsuariosComponent } from './features/admin/pages/usuarios/usuarios.component';
import { AdminDashboardComponent } from './features/admin/pages/dashboard/dashboard.component';
import { AdminHistorialComponent } from './features/admin/pages/historial/historial.component';
import { AdminMascotasComponent } from './features/admin/pages/mascotas/mascotas.component';
import { AdminAdopcionComponent } from './features/admin/pages/adopcion/adopcion.component';

export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'mascotas', component: MascotasComponent },
  { path: 'publicar', component: PublicarComponent, canActivate: [authGuard] },
  { path: 'adoptar', component: AdoptarComponent, canActivate: [authGuard] },
  { path: 'login', component: LoginComponent },
  {
    path: 'admin',
    canActivate: [adminGuard],
    children: [
      { path: '', component: AdminUsuariosComponent },
      { path: 'dashboard', component: AdminDashboardComponent },
      { path: 'mascotas', component: AdminMascotasComponent },
      { path: 'adopcion', component: AdminAdopcionComponent },
      { path: 'historial', component: AdminHistorialComponent },
    ],
  },
];
