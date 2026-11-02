
/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class AppLayout extends Component {
    static template = "coffee_shop_core.AppLayout";

    setup() {
        this.orm = useService("orm");

        this.state = useState({
            activeMenu: "shops",
            shops: [],
            loading: true,
            error: false,
        });

        onWillStart(async () => {
            await this.loadShops();
        });
    }

    async loadShops() {
        this.state.loading = true;
        this.state.error = false;

        try {
            this.state.shops = await this.orm.searchRead(
                "coffee.shop",
                [],
                ["name", "code", "manager_id", "active"]
            );
        } catch (error) {
            console.error("Failed to load coffee shops:", error);
            this.state.error = true;
        } finally {
            this.state.loading = false;
        }
    }

    createShop() {
        console.log("Create New Shop clicked");
    }

    selectMenu(menu) {
        this.state.activeMenu = menu;
    }
}
