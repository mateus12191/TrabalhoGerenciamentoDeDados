import os
import io
import base64
from PIL import Image

pasta_logos = "logos"
extensao = ".png"

# --- MAPEAMENTO DE CORREÇÃO ---
# Esquerda: Como pode aparecer no CSV ou nome duplicado
# Direita: Nome do arquivo OFICIAL que você quer usar (sem extensão)
NOMES_UNIFICADOS = {
    "Santos FC": "Santos",
    "Coritiba FC": "Coritiba",
    "Goiás EC": "Goiás",
    "EC Bahia": "Bahia",
    "EC Vitória": "Vitória",
    "Avaí FC": "Avaí",
    "Figueirense FC": "Figueirense",
    "Athletico-PR": "Atlético-PR", # Unificando grafia nova/antiga
    "America-MG": "América-MG",
    "Botafogo-RJ": "Botafogo"
}

def carregar_imagem_com_fundo_branco(caminho):
    try:
        img = Image.open(caminho)
        if img.mode in ('RGBA', 'LA'):
            fundo = Image.new('RGB', img.size, (255, 255, 255)) 
            fundo.paste(img, mask=img.split()[-1]) 
            return fundo
        else:
            return img.convert('RGB')
    except Exception as e:
        print(f"Erro ao abrir imagem {caminho}: {e}")
        return None

def imagem_para_base64(img):
    data = io.BytesIO()
    img.save(data, format='PNG')
    encoded_string = base64.b64encode(data.getvalue()).decode()
    return f"data:image/png;base64,{encoded_string}"

def carregaImagens(times_no_dataset, lista_nomes, lista_imagens):
    lista_nomes.clear()
    lista_imagens.clear()
    
    # Conjunto para rastrear times já processados e evitar repetidos
    times_ja_adicionados = set()

    # Ordena os times originais
    times_ordenados = sorted(list(times_no_dataset))

    for time_bruto in times_ordenados:
        # 1. Normaliza o nome (Ex: Se vier "Santos FC", vira "Santos")
        nome_arquivo = NOMES_UNIFICADOS.get(time_bruto.strip(), time_bruto.strip())
        
        # 2. Se já adicionamos esse time (ex: já adicionou Santos via "Santos", ignora o "Santos FC")
        if nome_arquivo in times_ja_adicionados:
            continue

        caminho_arquivo = os.path.join(pasta_logos, f"{nome_arquivo}{extensao}")
        
        # 3. Verifica se existe e carrega
        if os.path.exists(caminho_arquivo):
            img = carregar_imagem_com_fundo_branco(caminho_arquivo)
            if img:
                img_b64 = imagem_para_base64(img)
                
                lista_nomes.append(nome_arquivo) # Usamos o nome limpo na lista
                lista_imagens.append(img_b64)
                
                # Marca como processado
                times_ja_adicionados.add(nome_arquivo)
        else:
            # Opcional: print(f"Alerta: Imagem não encontrada para {nome_arquivo} (Origem: {time_bruto})")
            pass