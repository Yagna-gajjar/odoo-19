/** @odoo-module **/
/** @odoo-module **/

import { Component } from "@odoo/owl";
import { whenReady } from "@odoo/owl";
import { mountComponent } from "@web/env";

export class Root extends Component {
    static template = "brew_bean.Root";
    static props = {};
}

whenReady(() => {
    mountComponent(Root, document.body);
});