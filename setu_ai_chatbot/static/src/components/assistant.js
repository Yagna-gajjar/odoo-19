/** @odoo-module **/

import {Component, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {rpc} from "@web/core/network/rpc";

export class Assistant extends Component {
    static template = "setu_ai_chatbot.Assistant";

    setup() {
        this.state = useState({
            isOpen: false,
            message: "",
            messages: [],
            isTyping: false,
        });
    }

    toggleChat() {
        this.state.isOpen = !this.state.isOpen;
    }

    async testModelCatalog() {
        const result = await rpc(
            "/setu_ai_chatbot/test_model_catalog",
            {}
        );

        console.log("MODEL CATALOG:", result);
    }

    async testAIQuery() {
        const result = await rpc(
            "/setu_ai_chatbot/test_ai_query",
            {
                question: "How many customers do we have?"
            }
        );

        console.log("AI QUERY RESULT:", result);
    }

    async sendMessage() {
        const message = this.state.message.trim();

        if (!message) {
            return;
        }

        this.state.messages.push({
            text: message,
            type: "user",
        });

        this.state.message = "";
        this.state.isTyping = true;

        try {
            const result = await rpc(
                "/setu_ai_chatbot/message",
                {
                    message: message,
                }
            );

            if (result.success) {
                this.state.messages.push({
                    text: result.reply,
                    type: "assistant",
                });
            }
        } catch (error) {
            console.error("AI Assistant error:", error);

            this.state.messages.push({
                text: "Something went wrong while contacting the server.",
                type: "assistant",
            });
        } finally {
            this.state.isTyping = false;
        }
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