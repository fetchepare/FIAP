from __future__ import annotations
import logging
from src.azure_integration.cognitive_services import enviar_alerta_equipe
from src.models.schemas import Alerta, CategoriaRisco, NivelRisco, ResultadoFusao
logger=logging.getLogger(__name__)

ROTEAMENTO={
    CategoriaRisco.SAUDE_MATERNA:         "obstetricia-guarda@hospital.org",
    CategoriaRisco.COMPLICACAO_CIRURGICA: "centro-cirurgico-guarda@hospital.org",
    CategoriaRisco.VIOLENCIA_DOMESTICA:   "servico-social-psicologia@hospital.org",
    CategoriaRisco.SAUDE_PSICOLOGICA:     "psicologia-perinatal@hospital.org",
    CategoriaRisco.ANOMALIA_GINECOLOGICA: "ginecologia-guarda@hospital.org",
}
DISPARA={NivelRisco.ALTO,NivelRisco.CRITICO}

class MotorDeAlertas:
    def gerar_alertas(self, fusao: ResultadoFusao) -> list[Alerta]:
        return [Alerta(paciente_id=fusao.paciente_id,categoria=s.categoria,nivel=s.nivel,
            mensagem=f"[{s.nivel.value.upper()}] Paciente {fusao.paciente_id}: risco de {s.categoria.value.replace("_"," ")} (score={s.score:.2f}, modalidades: {", ".join(s.origem)}).",
            canal=ROTEAMENTO.get(s.categoria,"equipe-geral@hospital.org")) for s in fusao.scores if s.nivel in DISPARA]

    def despachar(self, alertas):
        for a in alertas:
            enviado=enviar_alerta_equipe(a.canal,f"[ALERTA {a.nivel.value.upper()}] {a.categoria.value}",a.mensagem)
            logger.info("%s: %s", "Despachado" if enviado else "Log offline", a.mensagem)
