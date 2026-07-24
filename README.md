# Bilion Luxure Bot 🎨💰

Bot Telegram de conteúdo +18 gerado por IA com pagamento PIX.

## Features
- 🎨 Geração de imagens via Stable Diffusion (Replicate)
- 🎬 Geração de vídeos via Wan 2.1 (RunPod) com fallback Replicate
- 💰 Pagamento automático via PIX (MercadoPago)
- 🪙 Sistema de moeda única: **coins**
- 📊 Dashboard financeiro com lucro real descontando taxas MP

## Commands
- `/start` - Menu principal
- `/img <prompt>` - Gerar imagem (🪙 1 coin)
- `/video <duracao> <prompt>` - Gerar vídeo (`4s` ou `8s`, 15 ou 30 coins)
- `/comprar` - Comprar pack de coins via PIX
- `/saldo` - Ver saldo
- `/finance` - [Admin] Dashboard financeiro com lucro real

## Planos

| Pack | Preço | Coins |
|------|-------|-------|
| ⚡ Básico | R$15 | 150 |
| 💎 Premium | R$30 | 350 |
| 👑 Ultra | R$60 | 800 |

## Custos de Geração
- Imagem: 🪙 1 coin (~R$0,011 de custo real)
- Vídeo 4s: 🪙 15 coins (~R$0,066 de custo real)
- Vídeo 8s: 🪙 30 coins (~R$0,132 de custo real)

## Margem
83% a 88% de margem líquida já descontando taxas do MercadoPago.

## Deploy (Railway)
1. Conecta o repo no Railway
2. Adiciona as variáveis de ambiente
3. Railway faz deploy automático

## Environment Variables
- `BOT_TOKEN` - Token do bot Telegram
- `REPLICATE_API_KEY` - API key do Replicate
- `MERCADOPAGO_ACCESS_TOKEN` - Token do MercadoPago
- `RUNPOD_API_KEY` - (opcional) API key do RunPod pra vídeo
- `RUNPOD_ENDPOINT_ID` - (opcional) Endpoint Wan 2.1 no RunPod
- `ADMIN_IDS` - Seu user ID do Telegram (pro /finance)
- `DATABASE_URL` - Caminho do SQLite
