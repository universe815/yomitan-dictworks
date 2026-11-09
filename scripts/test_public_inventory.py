"""Exercise release refusal independently from the metadata-only catalog check."""
import copy
import unittest
from check_public_inventory import validate_release_rights

class ReleaseRightsTests(unittest.TestCase):
    def setUp(self):
        self.entry={'id':'fixture','publication':{'status':'release-eligible','redistributionApproved':True,
            'license':'CC BY 4.0','evidence':'https://example.org/rights'}}

    def test_recorded_license_can_pass(self):
        validate_release_rights(self.entry)

    def test_disclaimer_does_not_approve_redistribution(self):
        e=copy.deepcopy(self.entry)
        e['publication'].update(status='metadata-and-tools-only',redistributionApproved=False)
        with self.assertRaisesRegex(ValueError,'not approved'):validate_release_rights(e)

    def test_license_name_without_evidence_is_rejected(self):
        self.entry['publication']['evidence']=None
        with self.assertRaisesRegex(ValueError,'evidence'):validate_release_rights(self.entry)

    def test_evidence_link_without_license_is_rejected(self):
        self.entry['publication']['license']=None
        with self.assertRaisesRegex(ValueError,'license'):validate_release_rights(self.entry)

if __name__=='__main__':unittest.main()
