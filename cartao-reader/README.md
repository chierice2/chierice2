# 📇 Leitor de Cartões de Visita (PWA)

Fotografe um cartão de visita, adicione uma observação e o app extrai **Empresa, Telefones, E-mails e País**
com o Claude (visão), mostra os dados para revisão e salva numa planilha do Google Sheets.

| Arquivo      | O que é                                                       |
|--------------|---------------------------------------------------------------|
| `index.html` | O app completo (HTML + Tailwind via CDN + JavaScript puro)    |
| `Code.gs`    | Webhook do Google Apps Script (`doPost`) que grava na planilha |

---

## 1. Criar a planilha e o webhook (≈ 3 min)

1. Crie uma planilha nova em <https://sheets.new>.
2. Menu **Extensões → Apps Script**.
3. Apague o conteúdo de `Código.gs` e cole todo o `Code.gs` deste repositório. Salve (💾).
   Deixe **um único arquivo** `.gs` no projeto (arquivos extras com o mesmo código causam conflito).
   Se o script não foi criado pelo menu da planilha, preencha `SPREADSHEET_ID` no topo do código.
4. *(Opcional, recomendado)* Preencha `SECRET_TOKEN` com uma senha qualquer, ex.: `const SECRET_TOKEN = 'minha-senha-123';`
5. No seletor de funções escolha **`testeManual`** → **Executar** → autorize o acesso à sua conta.
   Uma aba **"Cartões"** será criada com o cabeçalho e uma linha de teste (pode apagá-la).
6. **Implantar → Nova implantação** → ícone ⚙️ → **App da Web**:
   - *Executar como:* **Eu**
   - *Quem pode acessar:* **Qualquer pessoa**
7. Clique **Implantar** e copie a **URL do app da Web** (termina em `/exec`).

> Se você alterar o `Code.gs` depois, use **Implantar → Gerenciar implantações → ✏️ → Versão: Nova versão**
> para manter a mesma URL.

## 2. Obter a API Key da Anthropic

1. Acesse <https://console.anthropic.com> → **API Keys** → **Create Key**.
2. Recomendado: crie uma chave só para este app e defina um **limite de gastos** no console.

## 3. Colocar o app no celular

O `index.html` precisa ser servido por **HTTPS** (câmera e instalação como app exigem isso). Opções gratuitas:

- **GitHub Pages:** suba `index.html` num repositório → *Settings → Pages* → publique a branch.
- **Netlify Drop:** arraste a pasta `cartao-reader` em <https://app.netlify.com/drop>.
- **Vercel / Cloudflare Pages:** mesmo processo.

Depois, no celular:

1. Abra a URL publicada.
   - **Android (Chrome):** menu ⋮ → **Adicionar à tela inicial / Instalar app**.
   - **iPhone (Safari):** botão Compartilhar → **Adicionar à Tela de Início**.
2. Toque em ⚙️ e informe:
   - **API Key da Anthropic**
   - **URL do Webhook** (a URL `/exec` do passo 1)
   - **Token secreto** (se definiu `SECRET_TOKEN`)
3. Salve. As configurações ficam no `localStorage` do aparelho.

## 4. Uso

1. **Fotografar cartão** → confira a prévia (✕ Descartar / Tirar outra foto).
2. Escreva a observação (ex.: *"Pediu catálogo por e-mail"*).
3. **Processar Cartão** → revise/corrija os campos.
4. **Salvar na Planilha** → **Ler próximo cartão**.

---

## Detalhes técnicos

- **Modelo:** `claude-opus-5` por padrão (pode ser trocado nas configurações).
  A saída usa *structured outputs* (`output_config.format` com JSON Schema), então a resposta é sempre um JSON
  válido com `empresa`, `telefones`, `emails` e `pais`. O prompt de sistema também pede JSON estrito.
- **Idiomas/alfabetos:** o prompt trata cirílico, CJK, árabe etc.; nomes não latinos vêm com transliteração
  e os telefones são normalizados para `+DDI DDD número`.
- **Imagem:** redimensionada no aparelho para no máximo 1568 px e enviada como JPEG, o que reduz custo e tempo de upload.
- **Chamada direta do navegador:** usa o header `anthropic-dangerous-direct-browser-access: true`. Isso expõe a
  chave a quem tiver acesso ao aparelho/navegador, por isso vale usar uma chave dedicada e com limite de gastos.
  Para uso por várias pessoas, o ideal é mover a chamada da API para um backend (ex.: o próprio Apps Script).
- **Webhook:** o POST é enviado como `text/plain` contendo JSON. Isso evita o *preflight* CORS, que o Apps Script não suporta.
- **Planilha:** colunas `Data/Hora | Empresa | Telefones | Emails | País | Observações`. Vários telefones/e-mails
  ficam na mesma célula, um por linha. Textos que começam com `=`, `+`, `-` ou `@` são gravados como texto
  (evita que `+55…` vire fórmula).
