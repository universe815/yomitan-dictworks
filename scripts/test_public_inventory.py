"""Exercise the inventory entry validation independently from the catalog check."""
import copy
import unittest

from check_public_inventory import validate_entry


class InventoryEntryTests(unittest.TestCase):
    def setUp(self):
        self.entry = {
            "id": "fixture",
            "assetName": "Fixture-Yomitan.zip",
            "bytes": 1024,
            "sha256": "a" * 64,
            "searchRecords": 10,
            "publication": {
                "status": "released",
                "channel": "github-release",
                "releaseTag": "dictionary-assets",
                "releaseAssetName": "Fixture-Yomitan-2026.01.01.1.zip",
            },
        }

    def test_released_entry_passes(self):
        validate_entry(self.entry)

    def test_local_only_entry_passes(self):
        entry = copy.deepcopy(self.entry)
        entry["publication"] = {"status": "local-only", "note": "not published"}
        validate_entry(entry)

    def test_released_entry_requires_release_asset(self):
        entry = copy.deepcopy(self.entry)
        entry["publication"].pop("releaseAssetName")
        with self.assertRaises(KeyError):
            validate_entry(entry)

    def test_asset_name_must_be_flat(self):
        entry = copy.deepcopy(self.entry)
        entry["assetName"] = "nested/Fixture-Yomitan.zip"
        with self.assertRaises(AssertionError):
            validate_entry(entry)

    def test_unknown_status_is_rejected(self):
        entry = copy.deepcopy(self.entry)
        entry["publication"]["status"] = "pending"
        with self.assertRaises(AssertionError):
            validate_entry(entry)


if __name__ == "__main__":
    unittest.main()
