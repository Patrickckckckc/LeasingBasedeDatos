"""AutoLease Peru desktop application entry point."""

import customtkinter as ctk

from database import DatabaseManager
from ui import (
    ClientScreen,
    ContractScreen,
    LoginScreen,
    MaintenanceScreen,
    PaymentScreen,
    ReportsScreen,
    VehicleScreen,
)


class AutoLeaseApp(ctk.CTk):
    """Main window and navigation controller."""

    def __init__(self) -> None:
        super().__init__()
        self.title("AutoLease Peru | Gestión de Leasing Vehicular")
        self.geometry("1320x820")
        self.minsize(1100, 700)
        self.db = DatabaseManager()
        self.current_content: ctk.CTkBaseClass | None = None
        self.show_login()

    def show_login(self) -> None:
        self._clear()
        self.login_screen = LoginScreen(self, self.db, self.show_dashboard, self.destroy)
        self.login_screen.pack(fill="both", expand=True)

    def show_dashboard(self) -> None:
        self._clear()
        self.sidebar = ctk.CTkFrame(self, width=230, corner_radius=0, fg_color="#111827")
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        ctk.CTkLabel(self.sidebar, text="AutoLease Peru", font=ctk.CTkFont(size=22, weight="bold")).pack(
            pady=(32, 4), padx=15
        )
        ctk.CTkLabel(self.sidebar, text="Panel administrativo", text_color="#9ca3af").pack(pady=(0, 28))
        for text, screen in [
            ("Clientes", ClientScreen), ("Vehículos", VehicleScreen),
            ("Contratos", ContractScreen), ("Pagos", PaymentScreen),
            ("Mantenimientos", MaintenanceScreen), ("Reportes", ReportsScreen),
        ]:
            ctk.CTkButton(
                self.sidebar, text=text, anchor="w", fg_color="transparent",
                hover_color="#1f2937", command=lambda cls=screen: self.show_screen(cls),
            ).pack(fill="x", padx=14, pady=4)
        ctk.CTkButton(
            self.sidebar, text="Cerrar sesión", anchor="w", fg_color="#7f1d1d",
            hover_color="#991b1b", command=self.show_login,
        ).pack(side="bottom", fill="x", padx=14, pady=20)
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color="#f3f4f6")
        self.content.pack(side="right", fill="both", expand=True)
        self.show_screen(ClientScreen)

    def show_screen(self, screen_class: type[ctk.CTkFrame]) -> None:
        if self.current_content is not None:
            self.current_content.destroy()
        self.current_content = screen_class(self.content, self.db)
        self.current_content.pack(fill="both", expand=True)

    def _clear(self) -> None:
        for widget in self.winfo_children():
            widget.destroy()
        self.current_content = None


def main() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = AutoLeaseApp()
    app.mainloop()


if __name__ == "__main__":
    main()
