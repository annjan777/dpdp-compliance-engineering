# Attendance app for a government-run school (fixture).
# Stores pupils' names, class, daily attendance and a parent's mobile number; sends absence SMS to parents.
# Teachers can view all pupils in their class. Uses an SMS gateway hosted in India.
PUPIL_FIELDS = ["name", "class", "roll_no", "parent_mobile", "date_of_birth"]
def mark_absent(pupil, sms_gateway):
    sms_gateway.send(pupil["parent_mobile"], f"{pupil['name']} was absent today")
