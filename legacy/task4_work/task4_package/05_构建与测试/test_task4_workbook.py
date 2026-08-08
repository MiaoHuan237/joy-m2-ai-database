import re
import unittest
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[3]
PACKAGE_WORKBOOK = Path(__file__).resolve().parent.parent / "01_工作簿" / "微分应用45题_Task4处理结果_2026-08-08.xlsx"
WORKBOOK = (
    PACKAGE_WORKBOOK
    if PACKAGE_WORKBOOK.exists()
    else ROOT / "outputs" / "25757421d1d8" / "微分应用45题_Task4处理结果_2026-08-08.xlsx"
)


class Task4WorkbookTests(unittest.TestCase):
    def test_workbook_contains_expected_five_sheets_and_cjk_font(self):
        self.assertTrue(WORKBOOK.exists(), "Task 4 workbook has not been built")
        with ZipFile(WORKBOOK) as archive:
            names = set(archive.namelist())
            self.assertIn("xl/workbook.xml", names)
            self.assertIn("xl/styles.xml", names)
            workbook_xml = archive.read("xl/workbook.xml").decode("utf-8")
            sheet_names = re.findall(r'<(?:\w+:)?sheet name="([^"]+)"', workbook_xml)
            self.assertEqual(
                sheet_names,
                ["使用说明", "Task4处理清单", "45题总表", "标签与难度", "验收结果"],
            )
            styles_xml = archive.read("xl/styles.xml").decode("utf-8")
            self.assertIn("Microsoft YaHei", styles_xml)
            worksheet_xml = "".join(
                archive.read(name).decode("utf-8")
                for name in sorted(names)
                if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
            )
            self.assertIn("下一步", worksheet_xml)
            self.assertIn("确认本包后，才能生成正式导入候选", worksheet_xml)
            self.assertNotIn("#REF!", worksheet_xml)
            self.assertNotIn("approved_for_import</t>", worksheet_xml)


if __name__ == "__main__":
    unittest.main()
