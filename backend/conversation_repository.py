from .database import SQLiteDatabase


class ConversationRepository:
    def __init__(self, database: SQLiteDatabase):
        self.database = database

    def create(self) -> dict:
        with self.database.connection() as connection:
            cursor = connection.execute(
                "INSERT INTO conversations DEFAULT VALUES"
            )
            conversation_id = cursor.lastrowid
        conversation = self.get(conversation_id)
        if conversation is None:
            raise RuntimeError("La conversación recién creada no está disponible")
        return conversation

    def list(self) -> list[dict]:
        with self.database.connection() as connection:
            rows = connection.execute(
                """
                SELECT c.id, c.title, c.created_at, c.updated_at,
                       COUNT(m.id) AS message_count
                FROM conversations AS c
                LEFT JOIN messages AS m ON m.conversation_id = c.id
                GROUP BY c.id
                ORDER BY c.updated_at DESC, c.id DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get(self, conversation_id: int) -> dict | None:
        with self.database.connection() as connection:
            row = connection.execute(
                """
                SELECT id, title, created_at, updated_at
                FROM conversations
                WHERE id = ?
                """,
                (conversation_id,),
            ).fetchone()
            if row is None:
                return None
            messages = connection.execute(
                """
                SELECT id, role, content, created_at
                FROM messages
                WHERE conversation_id = ?
                ORDER BY id
                """,
                (conversation_id,),
            ).fetchall()
        return {**dict(row), "messages": [dict(message) for message in messages]}

    def exists(self, conversation_id: int) -> bool:
        with self.database.connection() as connection:
            row = connection.execute(
                "SELECT 1 FROM conversations WHERE id = ?",
                (conversation_id,),
            ).fetchone()
        return row is not None

    def get_recent_messages(
        self, conversation_id: int, limit: int
    ) -> list[dict[str, str]]:
        with self.database.connection() as connection:
            rows = connection.execute(
                """
                SELECT role, content
                FROM messages
                WHERE conversation_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (conversation_id, limit),
            ).fetchall()
        return [dict(row) for row in reversed(rows)]

    def add_exchange(
        self, conversation_id: int, user_message: str, assistant_message: str
    ):
        with self.database.connection() as connection:
            row = connection.execute(
                "SELECT title FROM conversations WHERE id = ?",
                (conversation_id,),
            ).fetchone()
            if row is None:
                raise KeyError(conversation_id)

            has_messages = connection.execute(
                "SELECT 1 FROM messages WHERE conversation_id = ? LIMIT 1",
                (conversation_id,),
            ).fetchone()
            connection.executemany(
                """
                INSERT INTO messages (conversation_id, role, content)
                VALUES (?, ?, ?)
                """,
                (
                    (conversation_id, "user", user_message),
                    (conversation_id, "assistant", assistant_message),
                ),
            )
            title = row["title"]
            if has_messages is None:
                title = user_message.splitlines()[0][:80]
            connection.execute(
                """
                UPDATE conversations
                SET title = ?,
                    updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                WHERE id = ?
                """,
                (title, conversation_id),
            )
