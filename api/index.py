def handler(request):
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/html'},
        'body': '<h1>🎉 It Works!</h1><p>Vercel Python serverless function is working!</p>'
    }
