import pytest
from playwright.sync_api import Page, expect

def test_example(page: Page):
    # 1️⃣ Go to your app
    page.goto("http://localhost:5000/")

    # 2️⃣ Upload file (fix: target input element, not button)
    page.locator("input[type='file']").set_input_files(r"C:\Users\Aseuro\Downloads\img6.jpg")

    # 3️⃣ Click Extract Text
    page.get_by_role("button", name="✨ Extract Text").click()

    # 4️⃣ Navigate different views
    page.get_by_role("button", name="📋 Table View").click()
    page.get_by_role("button", name="📄 JSON View").click()
    page.get_by_role("button", name="📄 Raw JSON").click()
    page.get_by_role("button", name="📋 View All Saved Forms").click()

    # 5️⃣ View and close a saved form
    page.locator("tr:nth-child(31) > .actions-cell > .btn-action.btn-view").click()
    page.get_by_role("button", name="✕").click()

    # 6️⃣ Edit a form
    page.locator("tr:nth-child(31) > .actions-cell > .btn-action.btn-edit").click()
    textbox = page.get_by_role("textbox", name="Form Data (JSON):")
    textbox.click()
    textbox.press("ArrowLeft")
    textbox.fill(
        "{\n"
        "  \"PatientInformation\": {\n"
        "    \"FirstName\": \"PAULA\",\n"
        "    \"LastName\": \"BUTLER\",\n"
        "    \"Address\": \"BENYON GROVE 715\",\n"
        "    \"City\": \"PARK RKHAMSTED AP 8765\",\n"
        "    \"EmailAddress\": \"PAULAB40@MAIL.COM\",\n"
        "    \"PhoneNumber\": \"149830232\",\n"
        "    \"DateOfBirth\": \"04081969\",\n"
        "    \"LanguagePreference\": \"English\",\n"
        "    \"InsurancePlanName\": \"STACLIFFESPAA\",\n"
        "    \"FacilityName\": \"YEOTAINTON\",\n"
        "    \"FacilityAddress\": \"LAKE CEYLN\",\n"
        "    \"FacilityCity\": \"CAPE RDEAU PT 95370\",\n"
        "    \"ClinicianName\": \"SPENCER BARKER\",\n"
        "    \"NPPIFF\": \"722127337\",\n"
        "    \"ClinicianSignature\": \"\",\n"
        "    \"Date\": \"05/02/2014\"\n"
        "  }\n"
        "}"
    )

    # 7️⃣ Save changes
    page.get_by_role("button", name="💾 Save Changes").click()
    page.once("dialog", lambda dialog: dialog.dismiss())

    # 8️⃣ Delete a form
    page.locator("tr:nth-child(30) > .actions-cell > .btn-action.btn-delete").click()

    # 9️⃣ Upload & Extract again
    page.get_by_role("button", name="⬆️ Upload & Extract").click()

    # 10️⃣ Download JSON
    with page.expect_download() as download_info:
        page.get_by_role("button", name="⬇️ Download JSON").click()
    download_json = download_info.value
    print(f"Downloaded JSON: {download_json.path()}")

    # 11️⃣ Copy data
    page.get_by_role("button", name="📋 Copy").click()

    # 12️⃣ Download CSV
    with page.expect_download() as download_csv_info:
        page.get_by_role("button", name="⬇️ Download CSV").click()
    download_csv = download_csv_info.value
    print(f"Downloaded CSV: {download_csv.path()}")

    # 13️⃣ Final view
    page.get_by_role("button", name="📄 JSON View").click()
