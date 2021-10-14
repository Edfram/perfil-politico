from perfil.core.management.commands import BaseCommand, get_city, get_party, parse_date
from perfil.core.models import Affiliation


class Command(BaseCommand):

    help = (
        "Import political party affiliation data from Brasil.io: "
        "https://brasil.io/dataset/eleicoes-brasil/filiados"
    )
    model = Affiliation
    statuses = {
        value.upper().replace(" ", "_"): key for key, value in Affiliation.STATUSES
    }

    @staticmethod
    def get_affiliation_if_exists(name, voter_id, party, city, started_in):
        affiliation_filter = {"party": party, "started_in": started_in, "voter_id": voter_id, "city": city}
        if len(str(voter_id)) > 10:
            affiliation_filter["name"] = name

        try:
            return Affiliation.objects.filter(**affiliation_filter).get()
        except Affiliation.MultipleObjectsReturned:
            print(f"Multiple objects returned for query: {affiliation_filter}. Changing only the first.")
            return Affiliation.objects.filter(**affiliation_filter).first()
        except Affiliation.DoesNotExist:
            pass

    @staticmethod
    def update_affiliation(
        affiliation,
        status,
        canceled_in,
        cancel_reason,
        ended_in,
        regularized_in,
        processed_in,
    ):
        updated_fields = []
        if affiliation.status != status:
            affiliation.status = status
            updated_fields.append("status")
        if affiliation.canceled_in != canceled_in:
            affiliation.canceled_in = canceled_in
            updated_fields.append("canceled_in")
        if affiliation.cancel_reason != cancel_reason:
            affiliation.cancel_reason = cancel_reason
            updated_fields.append("cancel_reason")
        if affiliation.ended_in != ended_in:
            affiliation.ended_in = ended_in
            updated_fields.append("ended_in")
        if affiliation.regularized_in != regularized_in:
            affiliation.regularized_in = regularized_in
            updated_fields.append("regularized_in")
        if affiliation.processed_in != processed_in:
            affiliation.processed_in = processed_in
            updated_fields.append("processed_in")
        affiliation.save(update_fields=updated_fields)

    def serialize(self, line):
        name = line["nome"]
        voter_id = line["titulo_eleitoral"]
        party = get_party(line["sigla_partido"], line["partido"])
        city = get_city(line["codigo_municipio"], line["municipio"], line["uf"])
        started_in = line["data_filiacao"]

        affiliation = self.get_affiliation_if_exists(name, voter_id, party, city, started_in)

        status = self.statuses.get(line["situacao"])
        canceled_in = parse_date(line["data_cancelamento"])
        cancel_reason = line["motivo_cancelamento"]
        ended_in = parse_date(line["data_desfiliacao"])
        regularized_in = parse_date(line["data_regularizacao"])
        processed_in = parse_date(line["data_processamento"])
        electoral_section = line["secao_eleitoral"] if line["secao_eleitoral"] != "" else None

        if not affiliation:
            return Affiliation(
                cancel_reason=cancel_reason,
                canceled_in=canceled_in,
                city=city,
                electoral_section=electoral_section,
                electoral_zone=line["zona_eleitoral"],
                ended_in=ended_in,
                name=name,
                party=party,
                processed_in=processed_in,
                regularized_in=regularized_in,
                started_in=started_in,
                status=status,
                voter_id=voter_id,
            )

        self.update_affiliation(
            affiliation,
            status,
            canceled_in,
            cancel_reason,
            ended_in,
            regularized_in,
            processed_in,
        )

    def post_handle(self):
        pass
