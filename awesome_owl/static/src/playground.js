import {Component, useState} from "@odoo/owl";

export class Playground extends Component {
    static template = "awesome_owl.Playground";

    setup() {
        this.totalCards = ['cat.jpg', 'monkey.jpeg', 'cake.jpg', 'panda.jpg', 'toothpaste.jpg', 'donut.jpg']
        const pairIds = this.totalCards.flatMap((_, index) => [index, index]);

        for (let i = pairIds.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [pairIds[i], pairIds[j]] = [pairIds[j], pairIds[i]];
        }
        this.state = useState({
            stop: false,
            time: {h: 0, m: 0, s: 0},
            cells: pairIds.map((pairId, index) => ({
                id: index,
                image: "/awesome_owl/static/img/back_image.jpg",
                pairId: pairId
            })),
            clickedCard: {},
            pointCount: 0,
            isWin: false,
            secondCardClicked: false,
            matchedCard: [],
            startAgain: false
        });
    }

    formattedValue(value) {
        return value.toString().padStart(2, "0");
    }

    toggleTimer() {
        if (this.state.startAgain) {
            const pairIds = this.totalCards.flatMap((_, index) => [index, index]);

            for (let i = pairIds.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [pairIds[i], pairIds[j]] = [pairIds[j], pairIds[i]];
            }
            this.state.stop = false
            this.state.time = {h: 0, m: 0, s: 0}
            this.state.cells = pairIds.map((pairId, index) => ({
                id: index,
                image: "/awesome_owl/static/img/back_image.jpg",
                pairId: pairId
            }))
            this.state.clickedCard = {}
            this.state.pointCount = 0
            this.state.isWin = false
            this.state.secondCardClicked = false
            this.state.matchedCard = []
            this.state.startAgain = false
            this.startTime(false)
        } else {
            this.startTime(!this.state.stop);

        }
    }

    startTime(timerStart) {
        if (timerStart) {
            this.timer = setInterval(() => {
                if (this.state.time.s < 60) {
                    this.state.time.s++
                } else {
                    this.state.time.s = 0
                    if (this.state.time.m < 60) {
                        this.state.time.m++
                    } else {
                        this.state.time.m = 0
                        this.state.h++
                    }

                }

            }, 100)
            this.state.stop = true
        } else {
            this.state.stop = false
            clearInterval(this.timer);
        }
    }

    handleClick(event) {
        const checkId = parseInt(event.currentTarget.id)
        if (this.state.stop && !this.state.secondCardClicked && !this.state.matchedCard.includes(checkId)) {
            const id = parseInt(event.currentTarget.id)
            const cell = this.state.cells.find(cell => cell.id === id);
            const pairId = event.currentTarget.querySelector('img').id
            if (Object.keys(this.state.clickedCard).length === 0) {
                cell.image = "/awesome_owl/static/img/" + this.totalCards[pairId];
                this.state.clickedCard = {
                    id: id,
                    image: this.totalCards[pairId],
                    pairId: pairId
                }
            } else {
                const id1 = parseInt(event.currentTarget.id)
                const pairId1 = event.currentTarget.querySelector('img').id
                const cell1 = this.state.cells.find(cell => cell.id === id1);
                cell1.image = "/awesome_owl/static/img/" + this.totalCards[pairId1];
                this.state.secondCardClicked = true
                setTimeout(() => {
                    if (this.state.clickedCard.pairId === pairId1) {
                        this.state.pointCount++
                        if (this.state.pointCount === 6) {
                            this.startTime(false)
                            this.state.isWin = true
                            this.state.startAgain = true
                        }
                        this.state.matchedCard.push(this.state.clickedCard.id)
                        this.state.matchedCard.push(this.totalCards[id])
                    } else {
                        const removeCell1 = this.state.cells.find(
                            cell => cell.id === this.state.clickedCard.id
                        );

                        const removeCell2 = this.state.cells.find(
                            cell => cell.id === id1
                        );
                        removeCell1.image = "/awesome_owl/static/img/back_image.jpg";
                        removeCell2.image = "/awesome_owl/static/img/back_image.jpg";
                    }
                    this.state.clickedCard = {}
                    this.state.secondCardClicked = false
                }, 600)
            }
        }
    }
}