# Bilion Luxure Bot 🎨

Bot Telegram de conteúdo +18 gerado por IA com assinatura PIX.

## Features
- 🎨 Geração de imagens via Stable Diffusion (Replicate)
- 💰 Pagamento automático via PIX (MercadoPago)
- 🪙 Sistema de coins e diamantes
- 📊 Dashboard de saldo

## Commands
- `/start` - Menu principal
- `/img <prompt>` - Gerar imagem (2 coins)
- `/video <prompt>` - Gerar vídeo (1-2 diamantes)
- `/comprar` - Comprar pack de coins
- `/saldo` - Ver saldo

## Deploy (Railway)
1. Conecta o repo no Railway
2. Adiciona as variáveis de ambiente no painel
3. Railway faz deploy automático

## Environment Variables
- `BOT_TOKEN` - Token do bot Telegram
- `REPLICATE_API_KEY` - API key do Replicate
- `MERCADOPAGO_ACCESS_TOKEN` - Token do MercadoPago
- `MERCADOPAGO_USER_ID` - User ID do MercadoPago
