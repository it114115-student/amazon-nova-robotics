/**
 * AWS SigV4 authenticated HTTP client for MCP
 * Based on the approach from https://pgrzesik.com/posts/securing-lambda-furls/
 * Uses AWS SDK v3 for signing requests
 */

import { fromNodeProviderChain } from "@aws-sdk/credential-providers";
import { HttpRequest } from "@smithy/protocol-http";
import { SignatureV4 } from "@smithy/signature-v4";
import { Sha256 } from "@aws-crypto/sha256-js";

export interface AwsAuthTransportOptions {
  url: string;
  region?: string;
  service?: string;
  sessionId?: string;
  timeout?: number;
}

export class AwsAuthTransport {
  private url: string;
  private region: string;
  private service: string;
  private sessionId?: string;
  private timeout: number;
  private credentials?: any;
  private signer?: SignatureV4;
  private isConnected = false;
  private credentialProvider?: any;
  private lastCredentialRefresh = 0;
  private credentialRefreshInterval = 14 * 60 * 1000; // 14 minutes

  constructor(options: AwsAuthTransportOptions) {
    this.url = options.url;
    this.region =
      options.region ||
      process.env.AWS_DEFAULT_REGION ||
      process.env.AWS_REGION ||
      "us-east-1";
    this.service = options.service || "lambda";
    this.sessionId = options.sessionId;
    this.timeout = options.timeout || 30000;
  }

  async connect(): Promise<void> {
    try {
      console.log(`🔐 Connecting to AWS authenticated MCP server: ${this.url}`);

      // Initialize AWS credential provider (reusable)
      this.credentialProvider = fromNodeProviderChain();
      await this.refreshCredentials();

      // Mark as connected before testing
      this.isConnected = true;

      // Test connection with a simple request
      await this.testConnection();

      console.log(`✅ Successfully connected to AWS authenticated MCP server`);
    } catch (error) {
      this.isConnected = false;
      console.error(
        `❌ Failed to connect to AWS authenticated MCP server:`,
        error
      );
      throw error;
    }
  }

  async close(): Promise<void> {
    this.isConnected = false;
    this.credentials = undefined;
    this.signer = undefined;
    console.log(`🔌 Disconnected from AWS authenticated MCP server`);
  }

  private async refreshCredentials(): Promise<void> {
    try {
      console.log("🔄 Refreshing AWS credentials...");

      // Get fresh credentials using the stored provider
      this.credentials = await this.credentialProvider();
      this.lastCredentialRefresh = Date.now();

      // Recreate the signer with fresh credentials
      this.signer = new SignatureV4({
        service: this.service,
        region: this.region,
        credentials: this.credentials,
        sha256: Sha256,
      });

      console.log("✅ AWS credentials refreshed successfully");
    } catch (error) {
      console.error("❌ Failed to refresh credentials:", error);
      throw new Error("Failed to refresh AWS credentials");
    }
  }

  private shouldRefreshCredentials(): boolean {
    const now = Date.now();
    return now - this.lastCredentialRefresh > this.credentialRefreshInterval;
  }

  async makeAuthenticatedRequest(payload: any): Promise<any> {
    if (!this.isConnected) {
      throw new Error("Transport not connected");
    }

    try {
      // Refresh credentials if they're stale
      if (this.shouldRefreshCredentials()) {
        await this.refreshCredentials();
      }

      const url = new URL(this.url);

      // Create the HTTP request
      const request = new HttpRequest({
        method: "POST",
        hostname: url.hostname,
        path: url.pathname,
        headers: {
          "Content-Type": "application/json",
          Host: url.hostname,
          ...(this.sessionId && { "X-Session-ID": this.sessionId }),
        },
        body: JSON.stringify(payload),
      });

      // Sign the request with fresh credentials
      const signedRequest = await this.signer!.sign(request);

      // Convert signed request to fetch request
      const fetchUrl = `${url.protocol}//${signedRequest.hostname}${signedRequest.path}`;
      const fetchOptions = {
        method: signedRequest.method,
        headers: signedRequest.headers,
        body: signedRequest.body,
      };

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(fetchUrl, {
        ...fetchOptions,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        const error = new Error(
          `HTTP ${response.status}: ${response.statusText} - ${errorText}`
        );

        // If we get a 403 with expired token, try refreshing credentials once
        if (response.status === 403 && errorText.includes("expired")) {
          console.log(
            "🔄 Token expired, attempting credential refresh and retry..."
          );
          await this.refreshCredentials();

          // Retry the request once with fresh credentials
          const retryRequest = new HttpRequest({
            method: "POST",
            hostname: url.hostname,
            path: url.pathname,
            headers: {
              "Content-Type": "application/json",
              Host: url.hostname,
              ...(this.sessionId && { "X-Session-ID": this.sessionId }),
            },
            body: JSON.stringify(payload),
          });

          const retrySignedRequest = await this.signer!.sign(retryRequest);
          const retryFetchUrl = `${url.protocol}//${retrySignedRequest.hostname}${retrySignedRequest.path}`;
          const retryFetchOptions = {
            method: retrySignedRequest.method,
            headers: retrySignedRequest.headers,
            body: retrySignedRequest.body,
          };

          const retryController = new AbortController();
          const retryTimeoutId = setTimeout(
            () => retryController.abort(),
            this.timeout
          );

          const retryResponse = await fetch(retryFetchUrl, {
            ...retryFetchOptions,
            signal: retryController.signal,
          });

          clearTimeout(retryTimeoutId);

          if (!retryResponse.ok) {
            const retryErrorText = await retryResponse.text();
            throw new Error(
              `HTTP ${retryResponse.status}: ${retryResponse.statusText} - ${retryErrorText}`
            );
          }

          return await retryResponse.json();
        }

        throw error;
      }

      const responseData = await response.json();
      return responseData;
    } catch (error) {
      console.error("AWS authenticated MCP request failed:", error);
      throw error;
    }
  }

  private async testConnection(): Promise<void> {
    // Test with a simple MCP list tools request
    const testMessage = {
      jsonrpc: "2.0",
      id: "test-connection",
      method: "tools/list",
      params: {},
    };

    const result = await this.makeAuthenticatedRequest(testMessage);

    if (result.error) {
      throw new Error(`Connection test failed: ${result.error.message}`);
    }

    console.log(
      `✅ Connection test successful, found ${
        result.result?.tools?.length || 0
      } tools`
    );
  }
}
