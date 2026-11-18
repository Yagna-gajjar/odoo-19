import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { CafeLayout } from "./components/cafe_layout";

export class CafeDashboard extends Component {
    static template = "brew_bean.CafeDashboard";

    static components = {
        CafeLayout,
    };
}

registry.category("public_components").add(
    "brew_bean.CafeDashboard",
    CafeDashboard
);