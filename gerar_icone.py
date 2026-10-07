from PIL import Image, ImageDraw

def criar_icone_terminal():
    size = (256, 256)
    # Fundo transparente
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Base arredondada escura (Chassi do Terminal)
    margin = 12
    draw.rounded_rectangle(
        [margin, margin, size[0] - margin, size[1] - margin],
        radius=40,
        fill=(14, 17, 25, 255),
        outline=(0, 210, 255, 255),
        width=8
    )

    # 2. Barra de topo da janela
    draw.rounded_rectangle(
        [margin + 4, margin + 4, size[0] - margin - 4, 68],
        radius=30,
        fill=(22, 27, 40, 255)
    )
    # Corrige a base da barra superior para ficar reta
    draw.rectangle(
        [margin + 4, 48, size[0] - margin - 4, 68],
        fill=(22, 27, 40, 255)
    )

    # 3. Botões estilo janela (Vermelho, Amarelo, Verde)
    draw.ellipse([36, 32, 50, 46], fill=(239, 68, 68, 255))
    draw.ellipse([60, 32, 74, 46], fill=(245, 158, 11, 255))
    draw.ellipse([84, 32, 98, 46], fill=(16, 185, 129, 255))

    # 4. Prompt de Comando ">" (Estilo CLI moderno)
    prompt_coords = [
        (45, 105),
        (85, 145),
        (45, 185)
    ]
    draw.line(prompt_coords, fill=(0, 210, 255, 255), width=16, joint="curve")

    # 5. Cursor de Terminal Retangular "_"
    draw.rectangle([105, 172, 165, 185], fill=(16, 185, 129, 255))

    # 6. Símbolo de Rede / Switch (Três nós interligados no canto inferior)
    draw.line([(185, 115), (215, 115)], fill=(0, 210, 255, 180), width=6)
    draw.line([(200, 115), (200, 140)], fill=(0, 210, 255, 180), width=6)
    draw.ellipse([178, 108, 192, 122], fill=(0, 210, 255, 255))
    draw.ellipse([208, 108, 222, 122], fill=(0, 210, 255, 255))
    draw.ellipse([193, 133, 207, 147], fill=(16, 185, 129, 255))

    # Guarda em múltiplos tamanhos padrão do Windows dentro do .ico
    icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save("app.ico", format="ICO", sizes=icon_sizes)
    print("Ícone 'app.ico' gerado com sucesso!")

if __name__ == "__main__":
    criar_icone_terminal()