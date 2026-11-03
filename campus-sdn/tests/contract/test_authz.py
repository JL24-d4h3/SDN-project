"""Pruebas de contrato de la autorización (sdn_common.authz).

La evaluación se comprueba contra la política real: la asignación del
rol al permiso y el tipo de recurso (C9). Son los casos que la Consola y
las I7 demostrarán en el slice.
"""

from sdn_common.authz import _allowed


def test_academic_cannot_read_alerts():
    assert not _allowed("academic", "P09", "alert")


def test_it_specialist_can_read_alerts():
    assert _allowed("it_specialist", "P09", "alert")


def test_network_admin_reads_network_alerts():
    assert _allowed("network_admin", "P09", "network_alert")


def test_super_admin_reads_any_alert():
    assert _allowed("super_admin", "P09", "alert")
    assert _allowed("super_admin", "P09", "network_alert")


def test_resource_type_outside_assignment_is_denied():
    assert not _allowed("it_specialist", "P09", "network_alert")


def test_academic_services_access():
    assert _allowed("academic", "P03", "academic_service")
    assert not _allowed("academic", "P03", "console")


def test_threshold_adjustment():
    assert _allowed("it_specialist", "P33", "detection_threshold")
    assert not _allowed("academic", "P33", "detection_threshold")


def test_unknown_role_or_permission_is_denied():
    assert not _allowed("nadie", "P09", "alert")
    assert not _allowed("academic", "P99", "alert")
