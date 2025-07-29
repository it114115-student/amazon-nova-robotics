import express from "express";
import { CognitoAuthService } from "../services/auth";
import {
  AuthMiddleware,
  AuthenticatedRequest,
} from "../services/auth-middleware";

export function createAuthRoutes(
  authService: CognitoAuthService,
  authMiddleware: AuthMiddleware
) {
  const router = express.Router();

  // Login endpoint
  router.post("/login", async (req, res) => {
    try {
      const { username, password } = req.body;

      if (!username || !password) {
        return res
          .status(400)
          .json({ error: "Username and password are required" });
      }

      const result = await authService.signIn(username, password);

      if (result.challengeName) {
        // Handle challenges like NEW_PASSWORD_REQUIRED
        return res.json({
          success: false,
          challengeName: result.challengeName,
          challengeParameters: result.challengeParameters,
          session: result.session,
        });
      }

      res.json({
        success: true,
        tokens: {
          accessToken: result.accessToken,
          idToken: result.idToken,
          refreshToken: result.refreshToken,
        },
      });
    } catch (error: any) {
      console.error("Login error:", error);
      res.status(400).json({
        error: error.name || "Login failed",
        message: error.message,
      });
    }
  });

  // Handle auth challenges (like new password required)
  router.post("/respond-to-auth-challenge", async (req, res) => {
    try {
      const { challengeName, session, challengeResponses } = req.body;

      if (!challengeName || !session || !challengeResponses) {
        return res
          .status(400)
          .json({ error: "Missing required challenge parameters" });
      }

      const result = await authService.respondToAuthChallenge(
        challengeName,
        session,
        challengeResponses
      );

      res.json({
        success: true,
        tokens: {
          accessToken: result.accessToken,
          idToken: result.idToken,
          refreshToken: result.refreshToken,
        },
      });
    } catch (error: any) {
      console.error("Challenge response error:", error);
      res.status(400).json({
        error: error.name || "Challenge response failed",
        message: error.message,
      });
    }
  });

  // Get current user info
  router.get(
    "/me",
    authMiddleware.verifyToken,
    async (req: AuthenticatedRequest, res) => {
      try {
        res.json({
          success: true,
          user: req.user,
        });
      } catch (error: any) {
        console.error("Get user error:", error);
        res.status(500).json({
          error: "Failed to get user info",
          message: error.message,
        });
      }
    }
  );

  // Forgot password
  router.post("/forgot-password", async (req, res) => {
    try {
      const { username } = req.body;

      if (!username) {
        return res.status(400).json({ error: "Username is required" });
      }

      await authService.forgotPassword(username);

      res.json({
        success: true,
        message: "Password reset code sent to your email",
      });
    } catch (error: any) {
      console.error("Forgot password error:", error);
      res.status(400).json({
        error: error.name || "Forgot password failed",
        message: error.message,
      });
    }
  });

  // Confirm forgot password
  router.post("/confirm-forgot-password", async (req, res) => {
    try {
      const { username, confirmationCode, newPassword } = req.body;

      if (!username || !confirmationCode || !newPassword) {
        return res.status(400).json({
          error: "Username, confirmation code, and new password are required",
        });
      }

      await authService.confirmForgotPassword(
        username,
        confirmationCode,
        newPassword
      );

      res.json({
        success: true,
        message: "Password reset successfully",
      });
    } catch (error: any) {
      console.error("Confirm forgot password error:", error);
      res.status(400).json({
        error: error.name || "Password reset confirmation failed",
        message: error.message,
      });
    }
  });

  // Admin routes - require authentication
  router.post(
    "/admin/create-user",
    authMiddleware.verifyToken,
    async (req: AuthenticatedRequest, res) => {
      try {
        const { username, email, temporaryPassword, permanent } = req.body;

        if (!username || !email || !temporaryPassword) {
          return res.status(400).json({
            error: "Username, email, and temporary password are required",
          });
        }

        await authService.adminCreateUser(
          username,
          email,
          temporaryPassword,
          permanent
        );

        res.json({
          success: true,
          message: "User created successfully",
        });
      } catch (error: any) {
        console.error("Create user error:", error);
        res.status(400).json({
          error: error.name || "User creation failed",
          message: error.message,
        });
      }
    }
  );

  router.delete(
    "/admin/users/:username",
    authMiddleware.verifyToken,
    async (req: AuthenticatedRequest, res) => {
      try {
        const { username } = req.params;

        if (!username) {
          return res.status(400).json({ error: "Username is required" });
        }

        await authService.adminDeleteUser(username);

        res.json({
          success: true,
          message: "User deleted successfully",
        });
      } catch (error: any) {
        console.error("Delete user error:", error);
        res.status(400).json({
          error: error.name || "User deletion failed",
          message: error.message,
        });
      }
    }
  );

  router.get(
    "/admin/users",
    authMiddleware.verifyToken,
    async (req: AuthenticatedRequest, res) => {
      try {
        const limit = parseInt(req.query.limit as string) || 60;
        const users = await authService.listUsers(limit);

        res.json({
          success: true,
          users,
        });
      } catch (error: any) {
        console.error("List users error:", error);
        res.status(500).json({
          error: "Failed to list users",
          message: error.message,
        });
      }
    }
  );

  return router;
}
