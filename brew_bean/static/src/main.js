import { whenReady } from "@odoo/owl";
import { mountComponent } from "@web/env";
import { Dashboard } from "./components/dashboard/dashboard";

const config = {
    dev: true,
    name: "Owl Tutorial"
};
whenReady(() => mountComponent(Dashboard, document.body, config));