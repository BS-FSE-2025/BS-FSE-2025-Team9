// The function i'm test
export const isValidId = (id) => {
    id = id.replace(/\D/g, '');  // Remove non-digit characters
    if (id.length !== 9) {  // Check if the length is 9
        return { isValid: false, error: "ID must have 9 digits exactly." };
    }
    return { isValid: true };
};

export const isValidEmail = (email) => {
    const sceEmailRegex = /^[a-zA-Z0-9._%+-]+@sce\.edu$/;  // ביטוי רגולרי לבדוק אימיילים
    if (!sceEmailRegex.test(email)) {
        return { isValid: false, error: "Invalid email format. It must end with @sce.edu"};
    }
    return { isValid: true };
};
