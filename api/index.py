"""
StrategyAI - Vercel Serverless Function
Minimal handler for testing
"""

# Define handler FIRST before any imports that might fail
def handler(event, context):
    """Vercel serverless handler"""
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/html'},
        'body': '<h1>StrategyAI - Handler Works!</h1><p>If you see this, the handler function is recognized.</p>'
    }
