import { Component } from "@odoo/owl";

export class CafeLayout extends Component {
    static template = "brew_bean.CafeLayout";

    static props = {
        title: { type: String, optional: true },
        children: { type: Object, optional: true },
    };
}