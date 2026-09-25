/**
 * Webhook do Leitor de Cartões de Visita.
 * Recebe um POST JSON do app e adiciona uma linha na planilha.
 *
 * Colunas: Data/Hora | Empresa | Telefones | Emails | País | Observações
 */

// Nome da aba onde os contatos serão gravados (criada automaticamente).
const SHEET_NAME = 'Cartões';

// Opcional: defina um token e informe o mesmo valor no app (Configurações).
// Deixe vazio ('') para não exigir token.
const SECRET_TOKEN = '';

const HEADERS = ['Data/Hora', 'Empresa', 'Telefones', 'Emails', 'País', 'Observações'];

function doPost(e) {
  const lock = LockService.getScriptLock();
  try {
    if (!e || !e.postData || !e.postData.contents) {
      return jsonResponse({ status: 'error', message: 'Corpo da requisição vazio.' });
    }

    let data;
    try {
      data = JSON.parse(e.postData.contents);
    } catch (err) {
      return jsonResponse({ status: 'error', message: 'JSON inválido.' });
    }

    if (SECRET_TOKEN && data.token !== SECRET_TOKEN) {
      return jsonResponse({ status: 'error', message: 'Token inválido.' });
    }

    const empresa = str(data.empresa);
    const telefones = list(data.telefones);
    const emails = list(data.emails);
    if (!empresa && !telefones.length && !emails.length) {
      return jsonResponse({ status: 'error', message: 'Nenhum dado de contato recebido.' });
    }

    lock.waitLock(10000);
    const sheet = getSheet();

    const dataHora = data.dataHora ? new Date(data.dataHora) : new Date();
    const row = [
      isNaN(dataHora.getTime()) ? new Date() : dataHora,
      safe(empresa),
      safe(telefones.join('\n')),
      safe(emails.join('\n')),
      safe(str(data.pais)),
      safe(str(data.observacoes))
    ];

    sheet.appendRow(row);
    const lastRow = sheet.getLastRow();
    sheet.getRange(lastRow, 1).setNumberFormat('dd/MM/yyyy HH:mm:ss');
    sheet.getRange(lastRow, 1, 1, HEADERS.length).setVerticalAlignment('top').setWrap(true);

    return jsonResponse({ status: 'success', row: lastRow });
  } catch (err) {
    return jsonResponse({ status: 'error', message: 'Erro no servidor: ' + err.message });
  } finally {
    try { lock.releaseLock(); } catch (ignored) {}
  }
}

// Permite testar a URL no navegador.
function doGet() {
  return jsonResponse({ status: 'ok', message: 'Webhook do Leitor de Cartões ativo.' });
}

function getSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) sheet = ss.insertSheet(SHEET_NAME);
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(HEADERS);
    sheet.getRange(1, 1, 1, HEADERS.length).setFontWeight('bold').setBackground('#0f172a').setFontColor('#ffffff');
    sheet.setFrozenRows(1);
    sheet.setColumnWidths(1, 1, 150);
    sheet.setColumnWidths(2, 1, 220);
    sheet.setColumnWidths(3, 2, 200);
    sheet.setColumnWidths(5, 1, 120);
    sheet.setColumnWidths(6, 1, 320);
  }
  return sheet;
}

function str(v) {
  return v == null ? '' : String(v).trim();
}

function list(v) {
  if (Array.isArray(v)) return v.map(str).filter(String);
  const s = str(v);
  return s ? s.split(/[\n;,]+/).map(str).filter(String) : [];
}

// Evita que textos iniciados por = + - @ sejam interpretados como fórmula.
function safe(s) {
  return /^[=+\-@]/.test(s) ? "'" + s : s;
}

function jsonResponse(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

// Execute esta função uma vez pelo editor para autorizar o script e testar a gravação.
function testeManual() {
  const res = doPost({
    postData: {
      contents: JSON.stringify({
        token: SECRET_TOKEN,
        empresa: 'Empresa Teste Ltda',
        telefones: ['+55 11 99999-9999', '+55 11 3333-4444'],
        emails: ['contato@teste.com.br'],
        pais: 'Brasil',
        observacoes: 'Registro de teste'
      })
    }
  });
  Logger.log(res.getContent());
}
