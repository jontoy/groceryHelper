const $toastBody = $('.toast-body');

const findCorrectElement = (classIdentifier, startingElement, maxDepth=4) => {
    let depth = 0;
    target = startingElement;
    while (!target.classList.contains(classIdentifier) && (depth <= maxDepth)){
        target = target.parentElement;
        depth += 1;
    }
    if (target.classList.contains(classIdentifier)){
        return target
    }
}

$(document.body).on('click', '.add-to-cart', async (e) => {
    e.preventDefault();
    const target = findCorrectElement('add-to-cart', e.target);
    if (target){
        const recipeId = target.dataset.recipeId;
        try{
            const res = await axios.post(`/api/recipes/${recipeId}/add-to-cart`);
            $toastBody.text(`${res.data.message}`);
            $('.toast').addClass('bg-success');
            $('.toast').removeClass('bg-danger');
            $('.toast').removeClass('hidden');
            $('.toast').toast('show');
        } catch (error) {
            $toastBody.text(`${error.response.data.message}`);
            $('.toast').removeClass('bg-success');
            $('.toast').addClass('bg-danger');

        }
        $('.toast').removeClass('hidden');
        $('.toast').toast('show');

    }
});