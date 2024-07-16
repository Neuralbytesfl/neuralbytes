const express = require('express');
const axios = require('axios');
const fs = require('fs');
const https = require('https');
const rateLimit = require('express-rate-limit');
const sanitizer = require('sanitizer');
const { exec } = require('child_process');
const cors = require('cors');  // Add CORS module

const app = express();
const PORT = 9091;

const sslOptions = {
    key: fs.readFileSync('certificates/server.key'),
    cert: fs.readFileSync('certificates/server.cert')
};

const config = JSON.parse(fs.readFileSync('config/config.json', 'utf-8'));
const apiKeys = new Set(config.apiKeys);

// Log loaded API keys for debugging
console.log("Loaded API keys:", Array.from(apiKeys));

// Load blocked IPs from file
let blockedIPs = new Set();
const blockedIPsFile = 'config/banip.txt';

function isValidIPv4Address(ip) {
    const ipv4Pattern = /^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
    return ipv4Pattern.test(ip);
}

function loadBlockedIPs() {
    if (fs.existsSync(blockedIPsFile)) {
        const data = fs.readFileSync(blockedIPsFile, 'utf-8');
        blockedIPs = new Set(data.split(',').map(ip => ip.trim()).filter(isValidIPv4Address));
        updateFirewallRules();
    }
}

function saveBlockedIPs() {
    fs.writeFileSync(blockedIPsFile, Array.from(blockedIPs).join(','));
    updateFirewallRules();
}

function updateFirewallRules() {
    blockedIPs.forEach(ip => {
        const ruleName = `BlockedIP_${ip.replace(/\./g, '_')}`;
        exec(`netsh advfirewall firewall show rule name="${ruleName}"`, (checkError, checkStdout, checkStderr) => {
            if (checkError || checkStderr.includes('No rules match')) {
                // Rule does not exist, create it
                exec(`netsh advfirewall firewall add rule name="${ruleName}" dir=in action=block remoteip=${ip}`, (addError, addStdout, addStderr) => {
                    if (addError) {
                        console.error(`Error creating firewall rule for ${ip}: ${addError.message}`);
                    }
                    if (addStderr) {
                        console.error(`Stderr for ${ip}: ${addStderr}`);
                    }
                    console.log(`Firewall rule created for ${ip}: ${addStdout}`);
                });
            }
        });
    });
}

function removeFirewallRule(ip) {
    const ruleName = `BlockedIP_${ip.replace(/\./g, '_')}`;
    exec(`netsh advfirewall firewall delete rule name="${ruleName}"`, (deleteError, deleteStdout, deleteStderr) => {
        if (deleteError) {
            console.error(`Error deleting firewall rule for ${ip}: ${deleteError.message}`);
        }
        if (deleteStderr) {
            console.error(`Stderr for ${ip}: ${deleteStderr}`);
        }
        console.log(`Firewall rule deleted for ${ip}: ${deleteStdout}`);
    });
}

loadBlockedIPs();

// Load whitelisted IPs from file
let whitelistedIPs = new Set();
const whitelistFile = 'config/whitelist.txt';

function loadWhitelistedIPs() {
    if (fs.existsSync(whitelistFile)) {
        const data = fs.readFileSync(whitelistFile, 'utf-8');
        whitelistedIPs = new Set(data.split(',').map(ip => ip.trim()).filter(isValidIPv4Address));
    }
}

loadWhitelistedIPs();

// Middleware to parse JSON bodies
app.use(express.json());

// Middleware to sanitize input
function sanitizeInput(req, res, next) {
    if (req.body && req.body.messages && req.body.messages[0] && req.body.messages[0].content) {
        req.body.messages[0].content = sanitizer.sanitize(req.body.messages[0].content).trim();
        console.log(`Sanitized prompt: ${req.body.messages[0].content}`); // Debug log
    }
    next();
}

// Track failed attempts
const failedAttempts = {};

function blockIP(ip) {
    blockedIPs.add(ip);
    saveBlockedIPs();
}

function unblockIP(ip) {
    if (blockedIPs.has(ip)) {
        blockedIPs.delete(ip);
        saveBlockedIPs();
        removeFirewallRule(ip);
    }
}

function isIPBlocked(ip) {
    loadBlockedIPs();
    return blockedIPs.has(ip);
}

// Middleware to log all requests
app.use((req, res, next) => {
    const clientIp = req.ip;
    logToFile(`Access - Method: ${req.method}, URL: ${req.originalUrl}, IP: ${clientIp}`);
    next();
});

// Function to verify API key complexity
function isValidApiKey(apiKey) {
    // Example complexity check: at least 8 characters, containing letters and numbers
    const regex = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$/;
    const isValid = regex.test(apiKey);
    console.log(`API key "${apiKey}" validity: ${isValid}`); // Debug log
    return isValid;
}

// CORS middleware
app.use(cors({
    origin: 'http://83.136.219.5',  // Replace with your front-end domain
    methods: 'GET,HEAD,PUT,PATCH,POST,DELETE',
    allowedHeaders: 'Content-Type,Authorization',
    credentials: true,
}));

// Middleware to authenticate requests
function authenticate(req, res, next) {
    const clientIp = req.ip;

    if (isIPBlocked(clientIp)) {
        logToFile(`Blocked IP attempt: ${clientIp}`);
        return res.status(403).send('FUCK YOU!!! 再见黑客 -- АМЕРИКА НЕ ЛЮБИТ ПУТИНА ');
    }

    if (whitelistedIPs.has(clientIp)) {
        console.log(`Whitelisted IP: ${clientIp}`); // Debug log
        return next();
    }

    const providedApiKey = req.query.api_key;
    console.log(`Received API key: "${providedApiKey}"`); // Debug log

    if (!providedApiKey || !apiKeys.has(providedApiKey) || !isValidApiKey(providedApiKey)) {
        logToFile(`Unauthorized access attempt: ${JSON.stringify(req.query)} from IP: ${clientIp}`);

        blockIP(clientIp);
        logToFile(`IP blocked due to failed attempt: ${clientIp}`);

        return res.status(401).send('Unauthorized');
    }

    next();
}

// Function to log messages to both console and file
function logToFile(message) {
    const logMessage = `${new Date().toISOString()} - ${message}\n`;
    console.log(logMessage);
    fs.appendFile('logs/ai.log', logMessage, (err) => {
        if (err) {
            console.error('Error writing to log file:', err);
        }
    });
}

// Rate limiting middleware
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100, // limit each IP to 100 requests per windowMs
    message: 'Too many requests from this IP, please try again after 15 minutes',
    handler: function (req, res, next, options) {
        const clientIp = req.ip;
        logToFile(`Rate limit exceeded: ${clientIp}`);
        res.status(options.statusCode).send(options.message);
    },
    skip: (req, res) => whitelistedIPs.has(req.ip) // Skip rate limiting for whitelisted IPs
});

// Apply rate limiting to all requests
app.use(limiter);

// Apply authentication middleware to all requests
app.use(authenticate);

// Route to proxy requests to Ollama service
app.post('/api/chat', sanitizeInput, async (req, res) => {
    const clientIp = req.ip;
    const providedApiKey = req.query.api_key;
    const userMessage = req.body.messages[0].content;
    const ollamaUrl = 'http://10.0.0.79:11434/api/chat';  // Replace with your Ollama service URL
    let assistantResponse = "";

    try {
        logToFile(`API Key: ${providedApiKey}, IP: ${clientIp}, Prompt: ${userMessage}`);
        const response = await axios.post(ollamaUrl, req.body, { responseType: 'stream' });

        response.data.on('data', (chunk) => {
            const chunkStr = chunk.toString();
            try {
                const jsonLine = JSON.parse(chunkStr);
                if (jsonLine.message && jsonLine.message.content) {
                    assistantResponse += jsonLine.message.content;
                }
            } catch (error) {
                console.error('Error parsing JSON chunk:', error);
            }
            res.write(chunk);
        });

        response.data.on('end', () => {
            logToFile(`Response: ${assistantResponse.trim()}`);
            res.end();
        });

        response.data.on('error', (error) => {
            logToFile(`Error during response streaming: ${error.message}`);
            res.status(500).send('Internal Server Error');
        });

    } catch (error) {
        logToFile(`Error proxying request: ${error.message}`);
        res.status(500).send('Internal Server Error');
    }
});

// Endpoint to unblock an IP (for demonstration purposes)
app.post('/unblock', (req, res) => {
    const { ip } = req.body;
    if (ip) {
        unblockIP(ip);
        logToFile(`IP unblocked: ${ip}`);
        return res.send(`IP ${ip} unblocked`);
    } else {
        return res.status(400).send('Bad Request: IP address is required');
    }
});

// Start the HTTPS server
https.createServer(sslOptions, app).listen(PORT, () => {
    logToFile(`Server running on port ${PORT}`);
});

// Polyfill for crypto.randomUUID
if (!crypto.randomUUID) {
    crypto.randomUUID = function() {
        return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
            (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
        );
    };
}
