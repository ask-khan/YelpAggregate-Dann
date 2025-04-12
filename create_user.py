from web.models import User

new_user = User()

new_user.email = input("Email: ")
new_user.set_password(input("Password: "))

new_user.is_admin = input("Admin? (y/n): ")[0].lower() == "y"

new_user.save()
print("Saved")
