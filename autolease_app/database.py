"""SQL Server data access layer for AutoLease Peru."""

from contextlib import contextmanager
from typing import Any, Iterator, Sequence

import pyodbc

from config import Settings, settings


class DatabaseError(RuntimeError):
    """Raised when an application database operation fails."""


class DatabaseManager:
    """Centralizes SQL Server connections and parameterized operations."""

    def __init__(self, app_settings: Settings = settings) -> None:
        self.settings = app_settings
        self._session_user = app_settings.default_user
        self._session_password = app_settings.default_password
        self._session_auth = app_settings.auth_mode

    def _connection_string(
        self,
        database: str | None = None,
        username: str | None = None,
        password: str | None = None,
        auth_mode: str | None = None,
    ) -> str:
        target_database = database or self.settings.database
        mode = (auth_mode or self._session_auth).lower()
        parts = [
            f"DRIVER={{{self.settings.driver}}}",
            f"SERVER={self.settings.server}",
            f"DATABASE={target_database}",
            f"TrustServerCertificate={'yes' if self.settings.trust_server_certificate else 'no'}",
        ]
        if mode in {"windows", "integrated"}:
            parts.append("Trusted_Connection=yes")
        else:
            parts.extend(
                [
                    f"UID={username if username is not None else self._session_user}",
                    f"PWD={password if password is not None else self._session_password}",
                ]
            )
        return ";".join(parts)

    def _connect(
        self,
        database: str | None = None,
        username: str | None = None,
        password: str | None = None,
        auth_mode: str | None = None,
    ) -> pyodbc.Connection:
        try:
            return pyodbc.connect(
                self._connection_string(database, username, password, auth_mode),
                timeout=8,
            )
        except pyodbc.Error as exc:
            raise DatabaseError(f"No se pudo conectar a SQL Server: {exc}") from exc

    @contextmanager
    def connection(self) -> Iterator[pyodbc.Connection]:
        connection = self._connect()
        try:
            yield connection
        finally:
            connection.close()

    def authenticate(self, username: str, password: str) -> None:
        """Validate SQL Server credentials and use them for this session."""
        if not username or not password:
            raise DatabaseError("Ingrese usuario y contraseña.")
        connection = self._connect(
            database=self.settings.database,
            username=username,
            password=password,
            auth_mode="sql",
        )
        connection.close()
        self._session_user = username
        self._session_password = password
        self._session_auth = "sql"

    def use_windows_session(self) -> None:
        """Switch operations to the current Windows identity."""
        self._connect(auth_mode="windows").close()
        self._session_auth = "windows"

    def select(
        self, query: str, parameters: Sequence[Any] = ()
    ) -> tuple[list[str], list[tuple[Any, ...]]]:
        try:
            with self.connection() as connection:
                cursor = connection.cursor()
                cursor.execute(query, parameters)
                columns = [column[0] for column in cursor.description or ()]
                return columns, [tuple(row) for row in cursor.fetchall()]
        except pyodbc.Error as exc:
            raise DatabaseError(f"Error al consultar datos: {exc}") from exc

    def execute(
        self, query: str, parameters: Sequence[Any] = ()
    ) -> int:
        try:
            with self.connection() as connection:
                cursor = connection.cursor()
                cursor.execute(query, parameters)
                affected = cursor.rowcount
                connection.commit()
                return affected
        except pyodbc.Error as exc:
            raise DatabaseError(f"Error al modificar datos: {exc}") from exc

    def insert(self, query: str, parameters: Sequence[Any] = ()) -> int:
        return self.execute(query, parameters)

    def update(self, query: str, parameters: Sequence[Any] = ()) -> int:
        return self.execute(query, parameters)

    def delete(self, query: str, parameters: Sequence[Any] = ()) -> int:
        return self.execute(query, parameters)
