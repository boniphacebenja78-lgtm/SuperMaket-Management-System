from werkzeug.security import generate_password_hash

print("========================================")
print("PASSWORD HASH GENERATOR")
print("========================================")

password = input("Enter the password you want to hash: ")

hashed_password = generate_password_hash(password)

print("\nGenerated password hash:")
print(hashed_password)

print("\nCopy this hash into the Employee.passwordHash field.")