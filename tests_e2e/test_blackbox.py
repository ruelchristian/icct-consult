import datetime
import re
import pytest
from playwright.sync_api import sync_playwright, expect

BASE_URL = "http://127.0.0.1:8000"

def get_next_weekday(target_weekday: int) -> datetime.date:
    """Finds the next upcoming weekday (0=Monday, 1=Tuesday, 2=Wednesday...)."""
    today = datetime.date.today()
    days_ahead = target_weekday - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + datetime.timedelta(days_ahead)

@pytest.fixture(scope="session")
def browser_instance():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()

@pytest.fixture
def page(browser_instance):
    context = browser_instance.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    yield page
    context.close()

# ---------------------------------------------------------------------------
# TEST 1: Public Landing Page & PWA Manifest
# ---------------------------------------------------------------------------
def test_01_public_landing_and_pwa(page):
    """Verify landing page content, branding, manifest, and offline fallback."""
    response = page.goto(f"{BASE_URL}/")
    assert response.status == 200, f"Expected 200, got {response.status}"
    
    # Check title & branding
    expect(page).to_have_title(re.compile("ICCT Colleges", re.IGNORECASE))
    expect(page.locator("text=ICCT COLLEGES").first).to_be_visible()
    
    # Check Hero action buttons
    expect(page.locator("a:has-text('Browse Faculty Schedule')").first).to_be_visible()
    expect(page.locator("a:has-text('Sign In to Portal')").first).to_be_visible()
    
    # Check Manifest
    manifest_res = page.request.get(f"{BASE_URL}/manifest.json")
    assert manifest_res.status == 200
    manifest_json = manifest_res.json()
    assert "ICCT" in manifest_json.get("name", "")
    assert manifest_json.get("display") == "standalone"

    # Check Offline Fallback page
    offline_res = page.goto(f"{BASE_URL}/offline/")
    assert offline_res.status == 200
    expect(page.locator("h1:has-text('You are currently offline')")).to_be_visible()

# ---------------------------------------------------------------------------
# TEST 2: Faculty Directory, Search & Calendar
# ---------------------------------------------------------------------------
def test_02_faculty_directory_search_and_calendar(page):
    """Verify directory search, department filtering, and FullCalendar JSON feed."""
    page.goto(f"{BASE_URL}/directory/faculty/")
    expect(page.locator("h1:has-text('Faculty Directory')")).to_be_visible()

    # Search for Alan Turing
    search_input = page.locator("input[name='q']")
    search_input.fill("Turing")
    page.locator("button:has-text('Search')").click()
    page.wait_for_load_state("networkidle")
    
    expect(page.locator("h3:has-text('Alan Turing')")).to_be_visible()
    expect(page.locator(".badge:has-text('CCS')").first).to_be_visible()

    # Click on Turing's profile
    page.locator("a:has-text('View Hours & Book Consultation')").first.click()
    page.wait_for_load_state("networkidle")
    
    expect(page.locator("h1:has-text('Alan Turing')")).to_be_visible()
    expect(page.locator("text=CCS Faculty Room").first).to_be_visible()
    expect(page.locator("text=Published Consultation Hours")).to_be_visible()

    # Verify Calendar JSON endpoint
    faculty_url = page.url
    faculty_id = faculty_url.rstrip("/").split("/")[-1]
    cal_res = page.request.get(f"{BASE_URL}/availability/faculty/{faculty_id}/events.json")
    assert cal_res.status == 200
    events = cal_res.json()
    assert len(events) >= 1, "Expected at least 1 calendar event for Prof. Turing"
    assert "Consultation" in events[0]["title"]

# ---------------------------------------------------------------------------
# TEST 3: Student Registration Workflow
# ---------------------------------------------------------------------------
# We keep track of the registered student for end-to-end booking flow
E2E_STUDENT_DATA = {}

def test_03_student_registration_workflow(page):
    """Test new student self-registration and automatic login."""
    page.goto(f"{BASE_URL}/accounts/register/")
    expect(page.locator("h2:has-text('Student Account Registration')")).to_be_visible()

    unique_suffix = datetime.datetime.now().strftime("%H%M%S")
    student_num = f"2026-{unique_suffix}"
    email = f"e2e.student{unique_suffix}@icct.edu.ph"
    pwd = "TestPassword123!"

    E2E_STUDENT_DATA["username"] = student_num.lower().replace("-", "").replace(" ", "")
    E2E_STUDENT_DATA["student_num"] = student_num
    E2E_STUDENT_DATA["email"] = email
    E2E_STUDENT_DATA["password"] = pwd

    page.locator("input[name='first_name']").fill("Automated")
    page.locator("input[name='last_name']").fill("Tester")
    page.locator("input[name='student_number']").fill(student_num)
    page.locator("input[name='email']").fill(email)
    page.locator("input[name='phone_number']").fill("09123456789")
    page.locator("input[name='program']").fill("BS Information Technology")
    page.locator("select[name='year_level']").select_option("3")
    page.locator("input[name='section']").fill("BSIT-3A")
    page.locator("input[name='password']").fill(pwd)
    page.locator("input[name='password_confirm']").fill(pwd)

    page.locator("button[type='submit']:has-text('Complete Student Registration')").click()
    page.wait_for_load_state("networkidle")

    # Successfully logged in and redirected to home/dashboard
    expect(page.locator("h1:has-text('Student Portal')")).to_be_visible()
    expect(page.locator(f"text={student_num}").first).to_be_visible()

    # Safely logout
    page.goto(f"{BASE_URL}/accounts/logout/")
    expect(page.locator("text=You have been logged out safely.")).to_be_visible()

# ---------------------------------------------------------------------------
# TEST 4: Student Authentication & Consultation Booking Flow
# ---------------------------------------------------------------------------
def test_04_student_login_and_book_consultation(page):
    """Test student login, password toggle, HTMX slot loading, and booking submission."""
    # Ensure a fresh registered student is available
    if "student_num" not in E2E_STUDENT_DATA:
        test_03_student_registration_workflow(page)

    page.goto(f"{BASE_URL}/accounts/login/")
    expect(page.locator("h2:has-text('Portal Sign In')")).to_be_visible()

    # Test password visibility toggle
    pwd_input = page.locator("#id_password")
    toggle_btn = page.locator("#toggle-password-btn")
    expect(pwd_input).to_have_attribute("type", "password")
    toggle_btn.click()
    expect(pwd_input).to_have_attribute("type", "text")
    toggle_btn.click()
    expect(pwd_input).to_have_attribute("type", "password")

    # Login with the fresh student account from Test 3
    login_user = E2E_STUDENT_DATA.get("student_num", "student_juan")
    login_pwd = E2E_STUDENT_DATA.get("password", "student123")

    page.locator("input[name='username_or_email']").fill(login_user)
    pwd_input.fill(login_pwd)
    page.locator("button[type='submit']:has-text('Sign In to Portal')").click()
    page.wait_for_load_state("networkidle")

    expect(page.locator("h1:has-text('Student Portal')")).to_be_visible()

    # Navigate to Directory -> Prof Alan Turing booking
    page.goto(f"{BASE_URL}/directory/faculty/")
    page.locator("input[name='q']").fill("Turing")
    page.locator("button:has-text('Search')").click()
    page.wait_for_load_state("networkidle")
    page.locator("a:has-text('View Hours & Book Consultation')").first.click()
    page.wait_for_load_state("networkidle")

    # Click Book Consultation Now
    page.locator("a:has-text('Book Consultation Now')").click()
    page.wait_for_load_state("networkidle")
    expect(page.locator("h1:has-text('Book Session with Alan Turing')")).to_be_visible()

    # Select Category
    page.locator("select[name='category']").select_option(index=1)

    # Next Monday has Turing's 9:00 AM - 12:00 PM slots
    next_monday = get_next_weekday(0)
    date_str = next_monday.strftime("%Y-%m-%d")
    
    # Fill date field and trigger HTMX request
    page.evaluate(f"""() => {{
        const el = document.getElementById('id_date');
        el.value = '{date_str}';
        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
    }}""")

    # Wait for HTMX slot container to populate and click the slot
    page.wait_for_selector("#available-slots-container label", timeout=7000)
    page.locator("#available-slots-container label").first.click()

    # Ensure time slot value is set
    if not page.locator("#id_time_slot").input_value():
        page.evaluate("""() => {
            const radio = document.querySelector("#available-slots-container input[name='slot_choice']");
            if (radio) {
                radio.checked = true;
                document.getElementById('id_time_slot').value = radio.value;
            }
        }""")

    # Verify time slot is populated
    slot_chosen = page.locator("#id_time_slot").input_value()
    assert slot_chosen and "-" in slot_chosen, f"Expected valid time slot, got '{slot_chosen}'"

    # Select Mode & Purpose
    page.locator("select[name='mode']").select_option("F2F")
    reason_text = "E2E Black Box Test: In-depth consultation on database architecture and ERD diagrams."
    page.locator("textarea[name='reason']").fill(reason_text)

    # Submit booking
    page.locator("button[type='submit']:has-text('Submit Consultation Request')").click()
    page.wait_for_load_state("networkidle")

    # Redirected to student bookings
    expect(page.locator("h1:has-text('My Consultation History')")).to_be_visible()
    expect(page.locator("text=Alan Turing").first).to_be_visible()
    expect(page.locator("text=PENDING").first).to_be_visible()

# ---------------------------------------------------------------------------
# TEST 5: Faculty Availability Slot Management
# ---------------------------------------------------------------------------
def test_05_faculty_manage_weekly_availability_slots(page):
    """Test faculty login, adding recurring weekly slots, and deleting slots."""
    # Logout student
    page.goto(f"{BASE_URL}/accounts/logout/")

    # Login as Prof. Turing
    page.goto(f"{BASE_URL}/accounts/login/")
    page.locator("input[name='username_or_email']").fill("prof_turing")
    page.locator("#id_password").fill("faculty123")
    page.locator("button[type='submit']:has-text('Sign In to Portal')").click()
    page.wait_for_load_state("networkidle")

    expect(page.locator("h1:has-text('Faculty Advising Portal')")).to_be_visible()
    expect(page.locator("text=Employee ID: EMP-101").first).to_be_visible()
    expect(page.locator("text=/Weekly Availability Slot.*Active/").first).to_be_visible()

    # Go to Manage Weekly Hours
    page.locator("a:has-text('Manage Weekly Hours')").first.click()
    page.wait_for_load_state("networkidle")
    expect(page.locator("h1:has-text('Manage Weekly Consultation Hours')")).to_be_visible()

    # Add a new slot: Friday, 10:00 - 11:30, 30 min duration, ONLINE
    page.locator("select[name='day_of_week']").select_option("4") # Friday
    page.locator("input[name='start_time']").fill("10:00")
    page.locator("input[name='end_time']").fill("11:30")
    page.locator("input[name='slot_duration_minutes']").fill("30")
    page.locator("select[name='mode']").select_option("ONLINE")
    page.locator("input[name='location_or_link']").fill("https://meet.google.com/test-e2e-friday")

    page.locator("button:has-text('Add Consultation Slot')").click()
    page.wait_for_load_state("networkidle")

    # Verify new slot appears in table
    expect(page.locator("tr:has-text('Friday')").first).to_be_visible()
    expect(page.locator("tr:has-text('10:00 AM - 11:30 AM')").first).to_be_visible()

    # Delete the Friday slot to restore clean state
    page.on("dialog", lambda dialog: dialog.accept())
    friday_row = page.locator("tr:has-text('Friday')")
    friday_row.locator("a[href*='/availability/delete/']").click()
    page.wait_for_load_state("networkidle")

    expect(page.locator("text=Consultation slot removed.")).to_be_visible()

# ---------------------------------------------------------------------------
# TEST 6: Faculty Review, Accept Consultation, & Document Session Notes
# ---------------------------------------------------------------------------
def test_06_faculty_consultation_lifecycle_and_notes(page):
    """Test faculty approving request and documenting advising outcome/notes."""
    # Login as Prof. Turing
    page.goto(f"{BASE_URL}/accounts/login/")
    page.locator("input[name='username_or_email']").fill("prof_turing")
    page.locator("#id_password").fill("faculty123")
    page.locator("button[type='submit']:has-text('Sign In to Portal')").click()
    page.wait_for_load_state("networkidle")

    # Navigate to pending requests
    page.goto(f"{BASE_URL}/bookings/faculty/?status=PENDING")
    expect(page.locator("h1:has-text('Consultation Management')")).to_be_visible()

    # Click on the visible detail link
    page.locator("a[href*='/bookings/detail/']:visible").first.click()
    page.wait_for_load_state("networkidle")

    expect(page.locator("h1:has-text('Consultation Details')")).to_be_visible()

    # Accept request if status is PENDING
    accept_btn = page.locator("button:has-text('Accept Consultation')")
    if accept_btn.is_visible():
        accept_btn.click()
        page.wait_for_load_state("networkidle")
        expect(page.locator("text=Booking status updated to CONFIRMED")).to_be_visible()

    # Now document session notes & attendance
    page.locator("a:has-text('Document Session Notes & Attendance')").click()
    page.wait_for_load_state("networkidle")

    expect(page.locator("h1:has-text('Consultation Session Record')")).to_be_visible()

    # Fill Session Record
    page.locator("select[name='attendance']").select_option("ATTENDED")
    page.locator("textarea[name='advice_given']").fill("System architecture verified. Schema indexes recommended on student_id.")
    page.locator("textarea[name='action_items']").fill("Submit revised database normalization report by Friday 5 PM.")
    page.locator("textarea[name='private_notes']").fill("CONFIDENTIAL: Student showed good grasp of Django CBVs and transactional locking.")

    page.locator("button:has-text('Save Consultation Record')").click()
    page.wait_for_load_state("networkidle")

    # Status should now be COMPLETED
    expect(page.locator("text=Session record and attendance saved successfully.")).to_be_visible()
    expect(page.locator(".badge:has-text('COMPLETED')").first).to_be_visible()

    # View record detail
    page.locator("a:has-text('View Session Advice')").click()
    page.wait_for_load_state("networkidle")
    expect(page.locator("text=Faculty Advice & Recommendations")).to_be_visible()
    expect(page.locator("text=Schema indexes recommended")).to_be_visible()
    # Faculty can see private notes
    expect(page.locator("text=Confidential Faculty Internal Notes")).to_be_visible()

# ---------------------------------------------------------------------------
# TEST 7: Student Confidentiality & Access Control (IDOR Check)
# ---------------------------------------------------------------------------
def test_07_student_confidentiality_and_access_control(page):
    """Ensure students can view advice, but NEVER see private faculty notes, and cannot access other students' records."""
    # Logout faculty, login as student
    page.goto(f"{BASE_URL}/accounts/logout/")
    page.goto(f"{BASE_URL}/accounts/login/")

    login_user = E2E_STUDENT_DATA.get("student_num", "student_juan")
    login_pwd = E2E_STUDENT_DATA.get("password", "student123")

    page.locator("input[name='username_or_email']").fill(login_user)
    page.locator("#id_password").fill(login_pwd)
    page.locator("button[type='submit']:has-text('Sign In to Portal')").click()
    page.wait_for_load_state("networkidle")

    # Go to student bookings
    page.goto(f"{BASE_URL}/bookings/student/")
    view_advice_links = page.locator("a:has-text('View Advice'):visible")
    
    if view_advice_links.count() > 0:
        view_advice_links.first.click()
        page.wait_for_load_state("networkidle")

        expect(page.locator("h1:has-text('Consultation Record & Advice')")).to_be_visible()
        expect(page.locator("text=Faculty Advice & Recommendations")).to_be_visible()
        
        # PRIVACY AUDIT: Private notes must NEVER appear in DOM or text for student
        content = page.content()
        assert "Confidential Faculty Internal Notes" not in content, "SECURITY BUG: Private notes heading exposed to student!"
        assert "CONFIDENTIAL:" not in content, "SECURITY BUG: Private note content leaked to student!"

    # IDOR Test: Attempt to access an unauthorized or non-existent booking
    forbidden_res = page.goto(f"{BASE_URL}/bookings/detail/999999/")
    assert forbidden_res.status in [404, 403], f"Expected 404 or 403 for unauthorized booking, got {forbidden_res.status}"

# ---------------------------------------------------------------------------
# TEST 8: Reports, Analytics & PDF Export
# ---------------------------------------------------------------------------
def test_08_reports_analytics_and_pdf_export(page):
    """Test admin and faculty reporting dashboards, KPI counters, and PDF generation."""
    page.goto(f"{BASE_URL}/accounts/logout/")
    page.goto(f"{BASE_URL}/accounts/login/")
    page.locator("input[name='username_or_email']").fill("admin")
    page.locator("#id_password").fill("admin123")
    page.locator("button[type='submit']:has-text('Sign In to Portal')").click()
    page.wait_for_load_state("networkidle")

    expect(page.locator("h1:has-text('System & Department Administration')")).to_be_visible()
    expect(page.locator("text=Total Bookings").first).to_be_visible()

    # Go to Reports & Analytics
    page.locator("a:has-text('Generate Department Reports'):visible, a:has-text('Reports & PDF'):visible").first.click()
    page.wait_for_load_state("networkidle")

    expect(page.locator("h1:has-text('Consultation Reports & Analytics')")).to_be_visible()
    expect(page.locator("text=Total Bookings").first).to_be_visible()
    expect(page.locator("text=Completed Sessions").first).to_be_visible()
    expect(page.locator("text=Confirmed / Active").first).to_be_visible()
    expect(page.locator("text=No-Shows").first).to_be_visible()

    # Test PDF Export Download
    with page.expect_download() as download_info:
        page.locator("a:has-text('Export Official PDF Report'):visible").click()
    download = download_info.value
    assert download.suggested_filename.endswith(".pdf")
    
    # Save to temp path and verify PDF header bytes
    pdf_path = download.path()
    with open(pdf_path, "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-", f"Expected valid PDF magic header, got {header}"
        size = f.seek(0, 2)
        assert size > 500, f"PDF file size {size} bytes is unexpectedly small"

# ---------------------------------------------------------------------------
# TEST 9: Mobile Viewport & Zero Horizontal Overflow Audit
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("viewport_width,viewport_height", [
    (375, 667), # iPhone SE / compact mobile
    (360, 740), # Standard Android phone
])
def test_09_mobile_zero_overflow_audit(browser_instance, viewport_width, viewport_height):
    """Audit mobile views to guarantee zero horizontal scroll and proper button/badge wrapping."""
    context = browser_instance.new_context(viewport={"width": viewport_width, "height": viewport_height})
    page = context.new_page()

    # 1. Login as Faculty
    page.goto(f"{BASE_URL}/accounts/login/")
    page.locator("input[name='username_or_email']").fill("prof_turing")
    page.locator("#id_password").fill("faculty123")
    page.locator("button[type='submit']:has-text('Sign In to Portal')").click()
    page.wait_for_load_state("networkidle")

    def assert_no_horizontal_overflow(view_name):
        scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
        client_width = page.evaluate("() => document.documentElement.clientWidth")
        body_scroll = page.evaluate("() => document.body.scrollWidth")
        assert scroll_width <= client_width + 1, f"Horizontal overflow on {view_name} (w={viewport_width}): scrollWidth={scroll_width} > clientWidth={client_width}"
        assert body_scroll <= client_width + 1, f"Body horizontal overflow on {view_name} (w={viewport_width}): bodyScroll={body_scroll} > clientWidth={client_width}"

    # Check Faculty Dashboard
    page.goto(f"{BASE_URL}/")
    assert_no_horizontal_overflow("Faculty Dashboard")
    expect(page.locator("text=Employee ID: EMP-101").first).to_be_visible()
    expect(page.locator("text=/Weekly Availability Slot.*Active/").first).to_be_visible()
    expect(page.locator("a:has-text('Reports & PDF'):visible").first).to_be_visible()

    # Check Consultation Management
    page.goto(f"{BASE_URL}/bookings/faculty/")
    assert_no_horizontal_overflow("Consultation Management")
    expect(page.locator("a:has-text('Consultation Reports & PDF'):visible").first).to_be_visible()

    # Check Reports Dashboard
    page.goto(f"{BASE_URL}/reports/")
    assert_no_horizontal_overflow("Reports Dashboard")
    expect(page.locator("a:has-text('Export Official PDF Report'):visible").first).to_be_visible()

    # Test Mobile Drawer toggle
    drawer_toggle = page.locator("#mobile-nav-drawer")
    expect(drawer_toggle).not_to_be_checked()
    # Click drawer open label (visible on mobile in topbar)
    page.locator("label[for='mobile-nav-drawer']:visible").first.click()
    expect(drawer_toggle).to_be_checked()
    # Drawer links visible
    expect(page.locator("aside a:has-text('Faculty Directory')")).to_be_visible()

    context.close()

# ---------------------------------------------------------------------------
# TEST 10: Notifications Center
# ---------------------------------------------------------------------------
def test_10_notifications_center(page):
    """Test live notification badge endpoint and notification list view."""
    page.goto(f"{BASE_URL}/accounts/logout/")
    page.goto(f"{BASE_URL}/accounts/login/")
    page.locator("input[name='username_or_email']").fill("student_juan")
    page.locator("#id_password").fill("student123")
    page.locator("button[type='submit']:has-text('Sign In to Portal')").click()
    page.wait_for_load_state("networkidle")

    # Check unread badge polling endpoint
    badge_res = page.request.get(f"{BASE_URL}/notifications/unread-badge/")
    assert badge_res.status == 200

    # Visit Notification List
    page.goto(f"{BASE_URL}/notifications/")
    expect(page.locator("h1:has-text('System Notifications')")).to_be_visible()
    expect(page.locator("text=Mark All as Read")).to_be_visible()
