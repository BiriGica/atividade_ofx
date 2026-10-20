from ofxparse import OfxParser
import psycopg2

def classificar_lancamento(descricao):
    desc = descricao.upper()
    if "ENERGIA" in desc: return "Energia"
    if "INTERNET" in desc: return "Internet"
    if "ALUGUEL" in desc: return "Aluguel"
    if "FOLHA" in desc: return "Folha de Pagamento"
    if "TI" in desc or "CLOUD" in desc: return "TI"
    if "RECEBIMENTO" in desc or "PIX" in desc: return "Recebimentos"
    return "Outros"

with open("extrato.ofx", "rb") as arquivo:
    ofx = OfxParser.parse(arquivo) 

entradas = 0
saidas = 0
qtd_movimentacoes = 0

print("--- PROCESSANDO EXTRATO ---")

try:
    conexao = psycopg2.connect(
    host="ep-lucky-math-b6ktvmff-pooler.c-2.sa-east-1.aws.neon.tech",
    database="neondb",
    user="neondb_owner",
    password="npg_c7B3AZLMDGES",
    sslmode="require"
)
    cursor = conexao.cursor()

    for t in ofx.account.statement.transactions: 
        qtd_movimentacoes += 1

        categoria = classificar_lancamento(t.memo)
        
        print(f"Lendo: {t.date.strftime('%d/%m/%Y')} | R$ {t.amount:.2f} | {t.memo}") 
        
        if t.amount > 0:
            entradas += t.amount
        else:
            saidas += t.amount

        query_verificacao = """
            SELECT id FROM movimentacoes 
            WHERE data_movimentacao = %s AND valor = %s AND descricao = %s;
        """
        cursor.execute(query_verificacao, (t.date.date(), float(t.amount), t.memo))
        resultado = cursor.fetchone()

        if resultado is None:

            query_insercao = """
                INSERT INTO movimentacoes (data_movimentacao, valor, descricao)
                VALUES (%s, %s, %s);
            """
            cursor.execute(query_insercao, (t.date.date(), float(t.amount), t.memo))
        else:
            print(f"  -> Transação ignorada: já existe no banco.")

    conexao.commit()
    print("\n[Sucesso] Sincronização com o NeonDB concluída!")

except (Exception, psycopg2.Error) as error:
    print(f"\nErro de conexão com o banco: {error}")

finally:
    if 'conexao' in locals() and conexao:
        cursor.close()
        conexao.close()

saldo = entradas + saidas

print("\n--- RESUMO ---")
print(f"Movimentações processadas: {qtd_movimentacoes}") 
print(f"Total de Entradas: R$ {entradas:.2f}") 
print(f"Total de Saídas: R$ {saidas:.2f}") 
print(f"Saldo: R$ {saldo:.2f}") 