import unittest
from unittest.mock import MagicMock

from agentic_shared.core.settings.secrets import SecuredStr
from agentic_shared.crosscut.crypto.cipher import FernetCipher
from agentic_shared.crosscut.crypto.settings import CryptoSettings
from agentic_shared.domains.persistence.repositories.sync_.pii_vault import (
    SqlAlchemyPiiVaultWriteRepositorySync,
)
from agentic_shared.domains.pii_vault.models import PiiVaultEntryDraft


class TestSqlAlchemyPiiVaultWriteRepositorySync(unittest.TestCase):
    def test_upsert_entries_encrypts_and_commits(self) -> None:
        session = MagicMock()
        cipher = FernetCipher(CryptoSettings(_env_file=None))
        repo = SqlAlchemyPiiVaultWriteRepositorySync(session, "tenant-a", cipher)
        repo.upsert_entries(
            [
                PiiVaultEntryDraft(
                    token="<PERSON_abc>",
                    entity_type="PERSON",
                    plaintext=SecuredStr("Jane VaultTest"),
                )
            ]
        )
        session.execute.assert_called_once()
        session.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
