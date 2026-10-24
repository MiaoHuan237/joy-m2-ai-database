"""Fixed V124 promotion: independent oracle, image/content integrity and gates."""
from dataclasses import replace
from functools import lru_cache
from pathlib import Path
import json, hashlib, shutil, sqlite3, tempfile, unittest
from unittest import mock

from joy_m2.config import PipelineConfig
from joy_m2.errors import PipelineError, PromotionError, InputFormatError
from joy_m2.models import VerificationReport, VerificationCheck
from joy_m2.ingest.v124_promotion_models import (
    V124PromotionBuildRequest, V124PromotionVerificationRequest,
    V124PublicationRequest, V124ReleasePromotionApproval)
from joy_m2.ingest import v124_promotion as builder
from joy_m2.ingest import v124_promotion_verification as verifier
from joy_m2.ingest.v124_verification import verify_chapter_candidate
from tests.fixtures.v124_promotion import (
    ROOT,selected_candidate,promotion_contract,fixture_release,tree,rebind,write_json,rewrite_sums)

CONFIG=PipelineConfig(ROOT)
STAGING=ROOT/"data/staging"

@lru_cache(maxsize=1)
def checked():
    request=selected_candidate()
    report=verify_chapter_candidate(request,CONFIG)
    assert report.status=="PASS" and len(report.checks)==24 and all(c.passed for c in report.checks)
    return request,report

class V124VerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate,cls.report=checked()
        cls.contract=promotion_contract()

    def verify(self,output):
        # Historical verifier is slow; cache only its already verified immutable
        # request in these formal-output mutation tests. Real gate runs unmocked.
        def verified(request,config):
            if request!=self.candidate or config!=CONFIG:
                raise AssertionError("test cache cannot validate other authority")
            return self.report
        with mock.patch.object(verifier,"verify_chapter_candidate",side_effect=verified,create=True):
            return verifier.verify_v124_promotion(V124PromotionVerificationRequest(
                output,self.candidate,self.contract),CONFIG)

    def test_independent_fixture_22_pass_and_zero_mutation(self):
        with tempfile.TemporaryDirectory(dir=STAGING) as tmp:
            output=fixture_release(Path(tmp)/"release",self.candidate,self.contract)
            before=tree(output);r=self.verify(output)
            self.assertIsInstance(r,VerificationReport,"independent verifier behavior missing")
            self.assertEqual(r.status,"PASS",r)
            self.assertEqual(len(r.checks),22)
            self.assertEqual(tree(output),before)

    def test_parsed_invalid_nested_manifests_fail_structurally(self):
        with tempfile.TemporaryDirectory(dir=STAGING) as tmp:
            output=fixture_release(Path(tmp)/"release",self.candidate,self.contract)
            path=output/"manifest.json";raw=path.read_bytes()
            for key,value in (("counts",True),("database",None),("images",[None]),
                              ("images",{}),("artifacts",[]),("batch_ledger",[1]),
                              ("promotion",[]),("candidate",{"generation":True})):
                with self.subTest(key=key,value=value):
                    data=json.loads(raw);data[key]=value;write_json(path,data)
                    r=self.verify(output)
                    self.assertIsInstance(r,VerificationReport)
                    self.assertEqual(r.status,"FAIL")
            path.write_bytes(b"{")
            with self.assertRaises(InputFormatError):self.verify(output)

    def test_rehashed_source_content_and_image_role_tampering_rejected(self):
        for field,value in (("question_text_original","invented"),
                            ("solution_original","invented solution"),
                            ("source_image_roles_json",'["solution"]'),
                            ("formal_image_paths_json",'["../../escape.jpg"]'),
                            ("tags_json",'["invented"]'),
                            ("difficulty_level",5)):
            with self.subTest(field=field),tempfile.TemporaryDirectory(dir=STAGING) as tmp:
                output=fixture_release(Path(tmp)/"release",self.candidate,self.contract)
                with sqlite3.connect(output/self.contract.database_filename) as db:
                    db.execute(f"UPDATE task14_v124_promoted_questions_v1 SET {field}=? WHERE formal_order=678",(value,))
                rebind(output,self.contract)
                self.assertEqual(self.verify(output).status,"FAIL")

    def test_parsed_manifest_unencodable_image_path_returns_fail(self):
        with tempfile.TemporaryDirectory(dir=STAGING) as tmp:
            output=fixture_release(Path(tmp)/"release",self.candidate,self.contract)
            path=output/"manifest.json";data=json.loads(path.read_bytes())
            data["images"][0]["relative_path"]="images/\ud800.jpg"
            path.write_bytes(json.dumps(data,ensure_ascii=True).encode("ascii"))
            try:
                report=self.verify(output)
            except UnicodeError as error:
                self.fail("parsed-invalid manifest leaked UnicodeError: "+str(error))
            self.assertEqual(report.status,"FAIL")

    def test_missing_changed_extra_or_linked_image_rejected(self):
        for change in ("missing","bytes","extra","link"):
            with self.subTest(change=change),tempfile.TemporaryDirectory(dir=STAGING) as tmp:
                output=fixture_release(Path(tmp)/"release",self.candidate,self.contract)
                m=json.loads((output/"manifest.json").read_bytes());p=output/m["images"][0]["relative_path"]
                if change=="missing":p.unlink()
                elif change=="bytes":p.write_bytes(b"wrong")
                elif change=="extra":(output/"images/rogue.jpg").write_bytes(b"rogue")
                else:
                    original=self.candidate.candidate_dir/m["images"][0]["relative_path"]
                    p.unlink();p.symlink_to(original)
                rewrite_sums(output)
                self.assertEqual(self.verify(output).status,"FAIL")

    def test_candidate_evidence_not_relabelled_as_human(self):
        with tempfile.TemporaryDirectory(dir=STAGING) as tmp:
            output=fixture_release(Path(tmp)/"release",self.candidate,self.contract)
            m=json.loads((output/"manifest.json").read_bytes())
            self.assertEqual([r["batch_candidate_count"] for r in m["batch_ledger"]],[16,14,4,14,11,32,20,3])
            self.assertTrue(all("grant_sha256" not in r["approval"] for r in m["batch_ledger"][:3]))
            self.assertTrue(all("grant_sha256" in r["approval"] for r in m["batch_ledger"][3:]))
            m["batch_ledger"][3]["approval"]["statement"]="USER APPROVED IMPORT BATCH invented"
            write_json(output/"manifest.json",m);rebind(output,self.contract)
            self.assertEqual(self.verify(output).status,"FAIL")

    def test_wrong_baseline_schema_rejected_after_rehash(self):
        with tempfile.TemporaryDirectory(dir=STAGING) as tmp:
            output=fixture_release(Path(tmp)/"release",self.candidate,self.contract)
            m=json.loads((output/"manifest.json").read_bytes())
            m["baseline"]["database_schema"]="task14-v124-formal-v1"
            write_json(output/"manifest.json",m);rebind(output,self.contract)
            self.assertEqual(self.verify(output).status,"FAIL")

class V124BuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate,cls.report=checked();cls.contract=promotion_contract()

    def setUp(self):
        # Only the repeated expensive historical check is cached. All builder,
        # filesystem, projection, identity and formal verification are real.
        for mod in (builder,verifier):
            def cache(req,config):
                if req!=self.candidate:raise AssertionError("different candidate")
                return self.report
            patch=mock.patch.object(mod,"verify_chapter_candidate",side_effect=cache,create=True)
            patch.start();self.addCleanup(patch.stop)

    def build(self,out,config=CONFIG):
        result=builder.build_v124_promotion(V124PromotionBuildRequest(self.candidate,out,self.contract),config)
        self.assertIsNotNone(result,"builder behavior missing")
        return result

    def test_two_builds_791_exact_content_and_72_images(self):
        with tempfile.TemporaryDirectory(dir=STAGING) as tmp:
            a=self.build(Path(tmp)/"a");b=self.build(Path(tmp)/"b")
            self.assertEqual(tree(a.database.path.parent),tree(b.database.path.parent))
            self.assertEqual(len(tree(a.database.path.parent)),76)
            self.assertEqual(len(a.images),72)
            self.assertEqual(a.release_digest,b.release_digest)
            with sqlite3.connect(a.database.path.as_uri()+"?mode=ro",uri=True) as db,sqlite3.connect(
                    (self.candidate.candidate_dir/self.candidate.contract.database_filename).as_uri()+"?mode=ro",uri=True) as old:
                rows=db.execute("SELECT * FROM formal_complete_questions_v124 ORDER BY formal_order").fetchall()
                self.assertEqual(len(rows),791);self.assertEqual(len({r[1] for r in rows}),791)
                self.assertEqual(rows[:677],old.execute("SELECT * FROM formal_complete_questions_v123 ORDER BY formal_order").fetchall())
                self.assertEqual(db.execute("SELECT * FROM task14_v124_promoted_questions_v1 ORDER BY formal_order").fetchall(),
                    [(*r[:30],"published",1) for r in old.execute("SELECT * FROM task14_v124_candidates_v1 ORDER BY aggregate_order")])
                self.assertTrue(all(r[-2:]==("published",1) for r in rows))
            for img in a.images:self.assertEqual(hashlib.sha256(img.path.read_bytes()).hexdigest(),img.sha256)

    def test_existing_overlap_symlink_and_historical_evidence_rejected(self):
        with tempfile.TemporaryDirectory(dir=STAGING) as tmp:
            root=Path(tmp);existing=root/"exists";existing.mkdir();(existing/"keep").write_text("keep")
            link=root/"link";link.symlink_to(root/"target",target_is_directory=True)
            paths=[existing,link,self.candidate.candidate_dir/"out",
                   STAGING/"vector-ch12-delegation-20261024-000001/out",
                   STAGING/"vector-ch12-intake-20261023-000001/out",
                   STAGING/"vector-ch12-mapping/out"]
            for out in paths:
                with self.subTest(out=out),self.assertRaises(PipelineError):self.build(out)
            self.assertEqual((existing/"keep").read_text(),"keep")

    def test_failed_candidate_verification_blocks_before_output(self):
        with tempfile.TemporaryDirectory(dir=STAGING) as tmp:
            out=Path(tmp)/"out"
            with mock.patch.object(builder,"verify_chapter_candidate",return_value=VerificationReport("FAIL",())):
                with self.assertRaises(PipelineError):self.build(out)
            self.assertFalse(out.exists())

    def test_failed_staging_verification_cleans_private_not_sources(self):
        with tempfile.TemporaryDirectory(dir=STAGING) as tmp:
            out=Path(tmp)/"out";before=tree(self.candidate.candidate_dir)
            with mock.patch.object(verifier,"verify_v124_promotion",return_value=VerificationReport("FAIL",())):
                with self.assertRaises(PromotionError):self.build(out)
            self.assertEqual(list(Path(tmp).iterdir()),[])
            self.assertEqual(tree(self.candidate.candidate_dir),before)

class V124PublicationTests(V124BuilderTests):
    def test_source_mutation_after_verification_never_reaches_formal_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();config=PipelineConfig(root);out=root/"data/staging/dry"
            built=self.build(out,config);target=root/"releases/V1.24"
            approval=V124ReleasePromotionApproval("V1.24",built.release_digest,
                "USER APPROVED RELEASE PROMOTION V1.24 "+built.release_digest)
            request=V124PublicationRequest(out,self.candidate,approval,self.contract)
            verify=verifier.verify_v124_promotion
            def change_after_check(req,cfg):
                report=verify(req,cfg)
                if req.release_dir==out:
                    self.assertEqual(report.status,"PASS")
                    with sqlite3.connect(out/self.contract.database_filename) as db:
                        db.execute("UPDATE task14_v124_promoted_questions_v1 SET question_text_original=? WHERE formal_order=678",("UNVERIFIED CHANGE",))
                return report
            with mock.patch.object(verifier,"verify_v124_promotion",side_effect=change_after_check),mock.patch.object(
                    builder,"atomic_rename_no_replace",wraps=builder.atomic_rename_no_replace) as rename:
                with self.assertRaises(PipelineError):builder.publish_v124_release(request,config)
                self.assertEqual(rename.call_count,0,"unverified bytes reached atomic publication")
            self.assertFalse(target.exists())

    def test_isolated_lifecycle_exact_approval_and_no_replace(self):
        # This fixture repo alone may be published. No real release approval.
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();config=PipelineConfig(root);out=root/"data/staging/dry"
            built=self.build(out,config)
            target=root/"releases/V1.24";self.assertFalse(target.exists())
            with self.assertRaises(PipelineError):
                V124PublicationRequest(out,self.candidate,None,self.contract)
            wrong=V124ReleasePromotionApproval("V1.24","0"*64,"USER APPROVED RELEASE PROMOTION V1.24 "+"0"*64)
            with self.assertRaises(PromotionError):
                builder.publish_v124_release(V124PublicationRequest(out,self.candidate,wrong,self.contract),config)
            self.assertFalse(target.exists())
            approval=V124ReleasePromotionApproval("V1.24",built.release_digest,
                "USER APPROVED RELEASE PROMOTION V1.24 "+built.release_digest)
            request=V124PublicationRequest(out,self.candidate,approval,self.contract)
            published=builder.publish_v124_release(request,config)
            self.assertIsNotNone(published,"publisher behavior missing")
            self.assertEqual(published.release_digest,built.release_digest)
            self.assertEqual(tree(target),tree(out))
            before=tree(root)
            with self.assertRaises(PipelineError):builder.publish_v124_release(request,config)
            self.assertEqual(tree(root),before)

    def test_publication_private_tamper_and_foreign_race(self):
        for case in ("tamper","race","final-fail","foreign-change"):
            with self.subTest(case=case),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp).resolve();config=PipelineConfig(root);out=root/"data/staging/dry"
                built=self.build(out,config);target=root/"releases/V1.24"
                a=V124ReleasePromotionApproval("V1.24",built.release_digest,
                    "USER APPROVED RELEASE PROMOTION V1.24 "+built.release_digest)
                req=V124PublicationRequest(out,self.candidate,a,self.contract)
                copy=shutil.copytree;verify=verifier.verify_v124_promotion
                def tamper(source,dest,**kw):
                    result=copy(source,dest,**kw);(Path(dest)/"rogue").write_text("x");return result
                def race(private,dest):
                    copy(private,dest);raise PromotionError("other writer won")
                def fail(r,c):
                    if r.release_dir==target:
                        if case=="foreign-change":(target/"foreign").write_text("retain")
                        return VerificationReport("FAIL",())
                    return verify(r,c)
                patch=(mock.patch.object(builder.shutil,"copytree",side_effect=tamper) if case=="tamper" else
                       mock.patch.object(builder,"atomic_rename_no_replace",side_effect=race) if case=="race" else
                       mock.patch.object(verifier,"verify_v124_promotion",side_effect=fail))
                with patch,self.assertRaises(PipelineError):builder.publish_v124_release(req,config)
                self.assertEqual(target.exists(),case in ("race","foreign-change"))
                if case=="race":self.assertEqual(tree(target),tree(out))
                if case=="foreign-change":self.assertEqual((target/"foreign").read_text(),"retain")
