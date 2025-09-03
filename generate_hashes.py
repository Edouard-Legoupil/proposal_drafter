from werkzeug.security import generate_password_hash

password_1 = 'password123'
password_2 = 'password456'

hashed_password_1 = generate_password_hash(password_1)
hashed_password_2 = generate_password_hash(password_2)

print(f"testuser1@example.com:{hashed_password_1}")
print(f"testuser2@example.com:{hashed_password_2}")
