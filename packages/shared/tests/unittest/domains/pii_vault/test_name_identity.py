import unittest

from agentic_shared.domains.pii_vault.name_identity import person_name_key, same_person_name


class TestPersonNameIdentity(unittest.TestCase):
    def test_hungarian_and_western_order_are_the_same_person(self) -> None:
        self.assertTrue(same_person_name("Dr. Varga Levente", "Dr. Levente Varga"))
        self.assertEqual(person_name_key("Varga Levente"), person_name_key("Levente Varga"))

    def test_single_surname_is_not_a_full_identity(self) -> None:
        self.assertFalse(same_person_name("Varga", "Levente Varga"))

    def test_different_people_do_not_match(self) -> None:
        self.assertFalse(same_person_name("Esther Szabo", "Levente Varga"))
