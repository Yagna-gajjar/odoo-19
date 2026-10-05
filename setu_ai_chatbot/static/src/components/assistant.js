/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class Assistant extends Component {
    static template = "setu_ai_chatbot.Assistant";

    setup() {
        this.state = useState({
            isOpen: false,
            message: "",
            messages: [],
        });
    }

    toggleChat() {
        this.state.isOpen = !this.state.isOpen;
    }

    sendMessage() {
        const message = this.state.message.trim();

        if (!message) {
            return;
        }

        this.state.messages.push({
            text: message,
            type: "user",
        });

        this.state.message = "";
    }

    onKeydown(event) {
        if (event.key === "Enter") {
            this.sendMessage();
        }
    }
}

registry.category("main_components").add("setu_ai_chatbot.Assistant", {
    Component: Assistant,
});