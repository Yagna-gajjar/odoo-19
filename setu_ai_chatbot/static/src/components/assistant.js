/** @odoo-module **/

import {Component, onWillStart, useEffect, useRef, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {rpc} from "@web/core/network/rpc";

let messageSequence = 0;

export class Analyst extends Component {
    static template = "setu_ai_chatbot.Analyst";
    static props = ["*"];

    setup() {
        this.thread = useRef("thread");
        this.state = useState({
            question: "",
            hints: "",
            conversationId: null,
            conversations: [],
            messages: [],
            isSending: false,
            isLoading: false,
            status: "",
        });
        onWillStart(() => this.loadConversations());
        useEffect(() => {
            const thread = this.thread.el;
            if (thread) {
                thread.scrollTop = thread.scrollHeight;
            }
        }, () => [this.state.messages.length, this.state.isSending]);
    }

    async loadConversations() {
        try {
            const result = await rpc("/setu_ai_chatbot/conversations", {});
            if (result && result.ok) {
                this.state.conversations = result.conversations || [];
            } else if (result && result.error) {
                this.state.status = result.error.message;
            }
        } catch {
            this.state.status = "Previous conversations could not be loaded.";
        }
    }

    newConversation() {
        if (this.state.isSending) {
            return;
        }
        this.state.conversationId = null;
        this.state.messages = [];
        this.state.status = "";
    }

    async openConversation(event) {
        if (this.state.isSending || this.state.isLoading) {
            return;
        }
        const conversationId = Number(event.currentTarget.dataset.conversationId);
        if (!Number.isInteger(conversationId) || conversationId <= 0) {
            this.state.status = "This conversation is not available.";
            return;
        }
        this.state.isLoading = true;
        this.state.status = "Loading conversation…";
        try {
            const result = await rpc("/setu_ai_chatbot/conversation", {
                conversation_id: conversationId,
            });
            if (!result || !result.ok) {
                this.state.status = (result && result.error && result.error.message) || "This conversation is not available.";
                return;
            }
            this.state.conversationId = result.conversation_id;
            this.state.messages = (result.messages || []).map((message) => this.historyMessage(message));
            this.state.status = "";
        } catch {
            this.state.status = "This conversation could not be loaded.";
        } finally {
            this.state.isLoading = false;
        }
    }

    async sendQuestion() {
        const question = this.state.question.trim();
        if (!question || this.state.isSending) {
            return;
        }
        this.state.question = "";
        this.state.isSending = true;
        this.state.status = "Working on your question…";
        this.state.messages.push({
            id: this.nextId(),
            role: "user",
            body: question,
        });
        try {
            const result = await rpc("/setu_ai_chatbot/ask", {
                question,
                conversation_id: this.state.conversationId,
                model_hints: this.hintList(),
            });
            this.applyAnswer(result, question);
            if (result && result.ok) {
                await this.loadConversations();
            }
        } catch {
            this.state.messages.push({
                id: this.nextId(),
                role: "assistant",
                error: "Something went wrong while contacting the server.",
            });
            if (!this.state.question) {
                this.state.question = question;
            }
        } finally {
            this.state.isSending = false;
            if (this.state.status === "Working on your question…") {
                this.state.status = "";
            }
        }
    }

    applyAnswer(result, question) {
        if (!result || !result.ok) {
            const error = (result && result.error) || {};
            if (error.type === "conversation") {
                this.state.conversationId = null;
            }
            this.state.messages.push({
                id: this.nextId(),
                role: "assistant",
                error: error.message || "The question could not be answered.",
            });
            if (!this.state.question) {
                this.state.question = question;
            }
            return;
        }
        this.state.conversationId = result.conversation_id;
        this.state.messages.push({
            id: this.nextId(),
            role: "assistant",
            explanation: result.explanation || "",
            table: result.table,
        });
    }

    historyMessage(message) {
        const item = {
            id: this.nextId(),
            role: message.role === "user" ? "user" : "assistant",
            body: message.body || "",
        };
        if (item.role === "assistant") {
            item.explanation = message.explanation || message.body || "";
            item.summary = message.summary || "";
        }
        return item;
    }

    hintList() {
        const hints = this.state.hints
            .split(",")
            .map((hint) => hint.trim())
            .filter((hint) => hint);
        return hints.length ? hints : null;
    }

    onKeydown(event) {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            this.sendQuestion();
        }
    }

    formatCell(value, type) {
        if (value === null || value === undefined || value === "") {
            return "";
        }
        if (type === "boolean" || typeof value === "boolean") {
            return value ? "Yes" : "No";
        }
        if (type === "integer") {
            const number = Number(value);
            return Number.isFinite(number) ? Math.trunc(number).toLocaleString() : String(value);
        }
        if (type === "float" || type === "monetary") {
            const number = Number(value);
            if (!Number.isFinite(number)) {
                return String(value);
            }
            return number.toLocaleString(undefined, {
                minimumFractionDigits: type === "monetary" ? 2 : 0,
                maximumFractionDigits: 2,
            });
        }
        if (type === "date" && typeof value === "string") {
            return this.formatDate(value);
        }
        if (type === "datetime" && typeof value === "string") {
            return this.formatDateTime(value);
        }
        return String(value);
    }

    formatDate(value) {
        const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
        if (!match) {
            return value;
        }
        const date = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
        return date.toLocaleDateString();
    }

    formatDateTime(value) {
        const match = /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})/.exec(value);
        if (!match) {
            return value;
        }
        const date = new Date(
            Number(match[1]),
            Number(match[2]) - 1,
            Number(match[3]),
            Number(match[4]),
            Number(match[5])
        );
        return date.toLocaleString();
    }

    nextId() {
        messageSequence += 1;
        return messageSequence;
    }
}

registry.category("actions").add("setu_ai_chatbot.analyst", Analyst);
