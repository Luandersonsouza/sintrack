from classificador import classificar_gravidade

test_cases = [
    ("Ônibus tomba", "Veículo tombou na curva deixando 10 feridos", "grave"),
    ("Colisão frontal", "Batida entre dois carros no centro", "moderado"),
    ("Trânsito lento", "Lentidão na via devido ao fluxo intenso", "leve")
]

for titulo, conteudo, esperado in test_cases:
    resultado = classificar_gravidade(titulo, conteudo)
    print(f"Teste: '{titulo}' | Esperado: {esperado} | Obtido: {resultado}")