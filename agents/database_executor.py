from typing import Any, Dict, List, Optional
import asyncio
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import logging
from contextlib import asynccontextmanager


class DatabaseExecutor:
    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url, echo=True)
        self.async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        self.logger = logging.getLogger("DatabaseExecutor")

    @asynccontextmanager
    async def get_session(self) -> AsyncSession:
        async with self.async_session() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                raise e

    async def execute_query(
        self, query: str, parameters: Optional[Dict[str, Any]] = None, transaction: bool = True
    ) -> List[Dict[str, Any]]:
        async with self.get_session() as session:
            try:
                if transaction:
                    async with session.begin():
                        result = await session.execute(text(query), parameters)
                        if result.returns_rows:
                            return [dict(row) for row in result]
                        return []
                else:
                    result = await session.execute(text(query), parameters)
                    if result.returns_rows:
                        return [dict(row) for row in result]
                    return []
            except Exception as e:
                self.logger.error(f"Query execution failed: {str(e)}")
                raise

    async def execute_batch(self, queries: List[Dict[str, Any]], transaction: bool = True) -> List[Dict[str, Any]]:
        results = []
        async with self.get_session() as session:
            try:
                if transaction:
                    async with session.begin():
                        for query_dict in queries:
                            result = await session.execute(text(query_dict["query"]), query_dict.get("parameters", {}))
                            if result.returns_rows:
                                results.append([dict(row) for row in result])
                            else:
                                results.append([])
                else:
                    for query_dict in queries:
                        result = await session.execute(text(query_dict["query"]), query_dict.get("parameters", {}))
                        if result.returns_rows:
                            results.append([dict(row) for row in result])
                        else:
                            results.append([])
                return results
            except Exception as e:
                self.logger.error(f"Batch execution failed: {str(e)}")
                raise

    async def execute_procedure(
        self, procedure_name: str, parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        async with self.get_session() as session:
            try:
                async with session.begin():
                    # Build procedure call
                    if parameters:
                        param_list = [f":{key}" for key in parameters.keys()]
                        query = f"CALL {procedure_name}({','.join(param_list)})"
                    else:
                        query = f"CALL {procedure_name}()"

                    result = await session.execute(text(query), parameters or {})
                    if result.returns_rows:
                        return [dict(row) for row in result]
                    return []
            except Exception as e:
                self.logger.error(f"Procedure execution failed: {str(e)}")
                raise

    async def analyze_query(self, query: str) -> Dict[str, Any]:
        async with self.get_session() as session:
            try:
                # Get query plan
                explain_query = f"EXPLAIN (FORMAT JSON, ANALYZE) {query}"
                result = await session.execute(text(explain_query))
                plan = result.scalar()

                # Get query statistics
                stats_query = """
                SELECT now() as timestamp,
                       pg_stat_statements.calls,
                       pg_stat_statements.total_time,
                       pg_stat_statements.rows,
                       pg_stat_statements.shared_blks_hit,
                       pg_stat_statements.shared_blks_read
                FROM pg_stat_statements
                WHERE query = :query
                """
                stats = await session.execute(text(stats_query), {"query": query})
                stats_row = stats.fetchone()

                return {
                    "plan": plan,
                    "statistics": dict(stats_row) if stats_row else None,
                    "analyzed_at": datetime.now().isoformat(),
                }
            except Exception as e:
                self.logger.error(f"Query analysis failed: {str(e)}")
                raise

    async def monitor_long_running_queries(self, threshold_seconds: int = 30) -> List[Dict[str, Any]]:
        async with self.get_session() as session:
            try:
                query = """
                SELECT pid,
                       now() - pg_stat_activity.query_start AS duration,
                       query,
                       state
                FROM pg_stat_activity
                WHERE (now() - pg_stat_activity.query_start) > interval ':threshold seconds'
                AND state != 'idle'
                AND state != 'idle in transaction'
                ORDER BY duration DESC
                """
                result = await session.execute(text(query), {"threshold": threshold_seconds})
                return [dict(row) for row in result]
            except Exception as e:
                self.logger.error(f"Query monitoring failed: {str(e)}")
                raise

    async def get_table_statistics(self, schema_name: str = "public") -> List[Dict[str, Any]]:
        async with self.get_session() as session:
            try:
                query = """
                SELECT
                    schemaname,
                    relname as table_name,
                    n_live_tup as row_count,
                    n_dead_tup as dead_rows,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables
                WHERE schemaname = :schema
                """
                result = await session.execute(text(query), {"schema": schema_name})
                return [dict(row) for row in result]
            except Exception as e:
                self.logger.error(f"Failed to get table statistics: {str(e)}")
                raise


if __name__ == "__main__":

    async def main():
        # Example usage
        executor = DatabaseExecutor("postgresql+asyncpg://user:pass@localhost/db")

        # Execute a simple query
        result = await executor.execute_query("SELECT * FROM users WHERE age > :age", {"age": 25})
        print("Query result:", result)

        # Execute a batch of queries
        batch_result = await executor.execute_batch(
            [
                {
                    "query": "INSERT INTO users (name, age) VALUES (:name, :age)",
                    "parameters": {"name": "John", "age": 30},
                },
                {"query": "SELECT * FROM users WHERE age > :age", "parameters": {"age": 25}},
            ]
        )
        print("Batch result:", batch_result)

        # Monitor long-running queries
        long_queries = await executor.monitor_long_running_queries(30)
        print("Long-running queries:", long_queries)

    asyncio.run(main())
