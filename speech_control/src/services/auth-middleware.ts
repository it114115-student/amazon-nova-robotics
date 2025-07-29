import { Request, Response, NextFunction } from "express";
import { CognitoAuthService } from "./auth";

export interface AuthenticatedRequest extends Request {
  user?: {
    username: string;
    email: string;
    emailVerified: boolean;
  };
}

export class AuthMiddleware {
  private authService: CognitoAuthService;

  constructor(authService: CognitoAuthService) {
    this.authService = authService;
  }

  /**
   * Middleware to verify JWT token in Authorization header
   */
  verifyToken = async (
    req: AuthenticatedRequest,
    res: Response,
    next: NextFunction
  ) => {
    try {
      const authHeader = req.headers.authorization;

      if (!authHeader || !authHeader.startsWith("Bearer ")) {
        return res.status(401).json({ error: "No token provided" });
      }

      const token = authHeader.split(" ")[1];

      // Verify the token
      await this.authService.verifyToken(token);

      // Get user information
      const user = await this.authService.getUser(token);
      req.user = user;

      next();
    } catch (error) {
      console.error("Token verification failed:", error);
      return res.status(401).json({ error: "Invalid token" });
    }
  };

  /**
   * Optional middleware - doesn't require authentication but sets user if token is valid
   */
  optionalAuth = async (
    req: AuthenticatedRequest,
    res: Response,
    next: NextFunction
  ) => {
    try {
      const authHeader = req.headers.authorization;

      if (authHeader && authHeader.startsWith("Bearer ")) {
        const token = authHeader.split(" ")[1];

        try {
          await this.authService.verifyToken(token);
          const user = await this.authService.getUser(token);
          req.user = user;
        } catch (error) {
          // Token is invalid, but we continue without user info
          console.log("Optional auth: Invalid token, continuing without user");
        }
      }

      next();
    } catch (error) {
      console.error("Optional auth error:", error);
      next();
    }
  };
}
