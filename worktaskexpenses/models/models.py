# -*- coding: utf-8 -*-

from odoo import models, fields, api
import base64
import mysql.connector

class worktaskexpenses(models.Model):
    _name = 'worktaskexpenses.worktaskexpenses'
    _description = 'Work Task to send data from odoo to Gastos Web app'

    def send_data_odoo_gastos(self):
        configs = None
        error = 0
        mysqlhost, mysqldb, mysqluser, mysqlpass = "", "", "", ""
        try:
            print("Obtener configuraciones")
            _confi_ = self.env['ir.config_parameter']
            conf = _confi_.search_read([('key','like','MYSQL')], ['key', 'value'])
            for c in conf:
                if c["key"] == "MYSQL_HOST":
                    mysqlhost = c["value"]
                elif c["key"] == "MYSQL_DATABASE":
                    mysqldb = c["value"]
                elif c["key"] == "MYSQL_PASSWORD":
                    decoded = base64.a85decode(c["value"])
                    message = decoded.decode('ascii')
                    mysqlpass = message
                else:
                    mysqluser = c["value"]
            if mysqlhost == "" or mysqldb == "" or mysqluser == "" or mysqlpass == "":
                print("No se puede continuar porque no existe configuracion para conectarse a la base de datos de Gastos")
                return None
            con = mysql.connector.connect(host=mysqlhost, database=mysqldb, user=mysqluser, password=mysqlpass)
            query = "SELECT company_id, payable_account_code FROM company_payable_account;"
            print("Obtener cuentas contables por compagnia")
            cursor = con.cursor()
            try:
                cursor.execute(query)
                configs = cursor.fetchall()
            except Exception as e1:
                print(e1)
            finally:
                if configs == None:
                    print("No se puede continuar porque no existe configuracion de cuentas contables por compagnia")
                    if con.is_connected():
                        con.close()
                        cursor.close()
                    return None
            print("Obtener compagnias que seran enviadas a Gastos (Todas las compagnias)")
            __comps__ = self.env['res.company']
            _comps_ = __comps__.search_read([('sequence','>=',0)], ['name', 'vat'])
            try:
                for c in _comps_:
                    query = "INSERT INTO sacompany(comp_id, comp_code, comp_name, tax_id_num) VALUES({}, '{}', '{}', '{}') ON DUPLICATE KEY UPDATE comp_code = VALUES(comp_code), comp_name = VALUES(comp_name), tax_id_num = VALUES(tax_id_num)".format(c["id"], c["vat"], c["name"], c["vat"])
                    cursor = con.cursor()
                    cursor.execute(query)
                con.commit()
            except Exception as e2:
                print(e2)
                con.rollback()
                print("Hubo un problema al crear o actualizar la compagnia {}".format(c["name"]))
            print("Obtener empleados que se enviaran a Gastos por cuenta contable")
            try:
                for k in configs:
                    _partners_ = self.env['res.partner']
                    _partners = _partners_.search_read([("company_id.id", "=", k[0]),("property_account_payable_id.code", "=", k[1])], ['id', 'name', 'vat', 'property_account_receivable_id', 'property_account_payable_id', 'company_id'])
                    for p in _partners:
                        query = "INSERT INTO apvend(id, vend_code, vend_name, comp_id, ap_acct_code) VALUES({}, '{}', '{}', {}, '{}') ON DUPLICATE KEY UPDATE vend_code = VALUES(vend_code), vend_name = VALUES(vend_name), comp_id = VALUES(comp_id), ap_acct_code = VALUES(ap_acct_code)".format(p["id"], p["vat"], p["name"], p["company_id"][0], p["property_account_payable_id"][1].split(" ")[0].strip())
                        try:
                            cursor.execute(query)
                            con.commit()
                        except Exception as e4:
                            print(e4)
                            con.rollback()
                            print("Hubo un problema al crear o actualizar el empleado {}".format(p["name"]))
            except Exception as e3:
                print(e3)
            finally:
                if con.is_connected():
                    con.close()
        except Exception as e:
            print(e)
            return e
