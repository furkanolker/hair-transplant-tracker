enum AppRole { admin, viewer }

class UserSession {
  const UserSession({required this.token, required this.role});

  final String token;
  final AppRole role;
}
