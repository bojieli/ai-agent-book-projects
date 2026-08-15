const axios = require('axios');
const config = require('./config');

async function testLLMEndpoint() {
    console.log('Testing LLM endpoint...');
    console.log(`URL: ${config.LLM_API_URL}`);
    console.log(`Model: ${config.LLM_MODEL}`);
    
    const testPrompt = "Tell me a short joke.";
    
    try {
        const response = await axios.post(
            config.LLM_API_URL,
            {
                model: config.LLM_MODEL,
                messages: [
                    { role: "user", content: testPrompt }
                ],
                stream: true,
                max_tokens: 100
            },
            {
                headers: {
                    'Authorization': `Bearer ${config.OPENAI_API_KEY}`,
                    'Content-Type': 'application/json',
                },
                responseType: 'stream'
            }
        );

        console.log('Connection established successfully');
        
        let fullResponse = '';
        
        response.data.on('data', chunk => {
            const lines = chunk.toString().split('\n');
            for (const line of lines) {
                if (line.trim() === '') continue;
                if (line.trim() === 'data: [DONE]') continue;
                if (!line.startsWith('data: ')) continue;
                
                try {
                    const jsonData = JSON.parse(line.replace('data: ', ''));
                    const content = jsonData.choices[0]?.delta?.content || '';
                    fullResponse += content;
                    process.stdout.write(content); // Stream the response
                } catch (e) {
                    console.error('Error parsing chunk:', e);
                    console.error('Raw chunk:', line);
                }
            }
        });

        response.data.on('end', () => {
            console.log('\n\nFull response received:', fullResponse);
            console.log('\nTest completed successfully');
        });

        response.data.on('error', (error) => {
            console.error('Stream error:', error);
        });

    } catch (error) {
        console.error('\nError testing LLM endpoint:', error.message);
        if (error.response) {
            console.error('Response status:', error.response.status);
            console.error('Response headers:', JSON.stringify(error.response.headers, null, 2));
        }
        
        // Log safe error properties
        const safeError = {
            message: error.message,
            name: error.name,
            stack: error.stack,
            code: error.code,
            status: error.status
        };
        console.error('\nError details:', JSON.stringify(safeError, null, 2));
    }
}

// Run the test
testLLMEndpoint(); 