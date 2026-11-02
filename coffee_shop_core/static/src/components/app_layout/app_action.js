/** @odoo-module **/

import { registry } from "@web/core/registry";
import { AppLayout } from "./app_layout";

registry.category("actions").add(
    "coffee_shop_core.app",
    AppLayout
);