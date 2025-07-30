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

    constructor(options: AwsAuthTransportOptions) {
        this.url = options.url;
        this.region = options.region || process.env.AWS_DEFAULT_REGION || process.env.AWS_REGION || 'us-east-1';
        this.service = options.service || 'lambda';
        this.sessionId = options.sessionId;
        this.timeout = options.timeout || 30000;
    }

    async connect(): Promise<void> {
        try {
            console.log(`🔐 Connecting to AWS authenticated MCP server: ${this.url}`);

            // Initialize AWS credentials
            const credentialProvider = fromNodeProviderChain();
            this.credentials = await credentialProvider();

            // Initialize the signer
            this.signer = new SignatureV4({
                service: this.service,
                region: this.region,
                credentials: this.credentials,
                sha256: Sha256,
            });

            // Mark as connected before testing
            this.isConnected = true;

            // Test connection with a simple request
            await this.testConnection();

            console.log(`✅ Successfully connected to AWS authenticated MCP server`);
        } catch (error) {
            this.isConnected = false;
            console.error(`❌ Failed to connect to AWS authenticated MCP server:`, error);
            throw error;
        }
    }

    async close(): Promise<void> {
        this.isConnected = false;
        this.credentials = undefined;
        this.signer = undefined;
        console.log(`🔌 Disconnected from AWS authenticated MCP server`);
    }

    async makeAuthenticatedRequest(payload: any): Promise<any> {
        if (!this.isConnected || !this.signer) {
            throw new Error('Transport not connected');
        }

        try {
            const url = new URL(this.url);

            // Create the HTTP request
            const request = new HttpRequest({
                method: 'POST',
                hostname: url.hostname,
                path: url.pathname,
                headers: {
                    'Content-Type': 'application/json',
                    'Host': url.hostname,
                    ...(this.sessionId && { 'X-Session-ID': this.sessionId }),
                },
                body: JSON.stringify(payload),
            });

            // Sign the request
            const signedRequest = await this.signer.sign(request);

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
                throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
            }

            const responseData = await response.json();
            return responseData;

        } catch (error) {
            console.error('AWS authenticated MCP request failed:', error);
            throw error;
        }
    }

    private async testConnection(): Promise<void> {
        // Test with a simple MCP list tools request
        const testMessage = {
            jsonrpc: '2.0',
            id: 'test-connection',
            method: 'tools/list',
            params: {},
        };

        const result = await this.makeAuthenticatedRequest(testMessage);

        if (result.error) {
            throw new Error(`Connection test failed: ${result.error.message}`);
        }

        console.log(`✅ Connection test successful, found ${result.result?.tools?.length || 0} tools`);
    }
}