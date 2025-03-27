# Factory: `UserFactory`

This file defines a test data factory using the `factory_boy` library for quickly generating `User` model instances in tests.

---

## `UserFactory`

```python
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: f"user{n}")
    password = factory.PostGenerationMethodCall('set_password', 'password123')
```

### Details

- **Base**: `DjangoModelFactory` from `factory_boy`
- **Model**: Dynamically resolves to Django’s current user model
- **Fields**:
  - `username`: Auto-incrementing usernames (e.g., `user0`, `user1`, ...)
  - `password`: Uses Django's `set_password()` to hash `password123`

---

## Use Case

This factory is used in unit or integration tests to easily create user accounts.

```python
user = UserFactory()
assert user.check_password("password123")
```

No need to manually create or clean up users in test setups.

---