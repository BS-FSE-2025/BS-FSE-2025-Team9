const express = require('express');
const Document = require('../models/Document');
const ExcelJS = require('exceljs'); // Import ExcelJS
const fs = require('fs');
const path = require('path');

const router = express.Router();


// Helper function to decode and save base64 image
const saveBase64Image = (base64String, student_id) => {
    // Validate and decode the base64 string
    const matches = base64String.match(/^data:([A-Za-z-+\/]+);base64,(.+)$/);
    if (!matches || matches.length !== 3) {
        throw new Error('Invalid base64 string');
    }

    const fileType = matches[1]; // Extract the file type
    const base64Data = matches[2]; // Extract the base64 encoded data
    const extension = fileType.split('/')[1]; // Extract the file extension

    // Generate a unique file name
    const fileName = `license-${student_id}-${Date.now()}.${extension}`;
    const filePath = path.join('uploads', fileName);

    // Ensure the uploads directory exists
    if (!fs.existsSync('uploads')) {
        fs.mkdirSync('uploads');
    }

    // Save the file to the uploads directory
    fs.writeFileSync(filePath, base64Data, 'base64');
    return fileName; // Return the file name
};



// Route to create a new document
router.post('/documents', async (req, res) => {
    try {
        const { parking_application } = req.body;

        // Validate required fields
        if (
            !parking_application.first_name ||
            !parking_application.last_name ||
            !parking_application.email ||
            !parking_application.student_id ||
            !parking_application.phone_number ||
            !parking_application.Study_Department ||
            !parking_application.car_type ||
            !parking_application.car_number ||
            !parking_application.license_image
        ) {
            return res.status(400).json({ message: 'All fields are required.' });
        }

        // Save the license image and generate the file name
        const fileName = saveBase64Image(
            parking_application.license_image,
            parking_application.student_id
        );

        // Create a new document in the database
        const newDocument = new Document({
            first_name: parking_application.first_name,
            last_name: parking_application.last_name,
            email: parking_application.email,
            student_id: parking_application.student_id,
            phone_number: parking_application.phone_number,
            Study_Department: parking_application.Study_Department,
            car_type: parking_application.car_type,
            car_number: parking_application.car_number,
            licenseImage: fileName,
            is_won: false            

        });

        await newDocument.save();
        console.log("Document saved successfully");

        res.status(201).json({
            message: 'Document created successfully',
            document: newDocument,
        });
    } catch (err) {
        console.error("Error saving document:", err);
        res.status(400).json({ message: 'Error creating document', error: err.message });
    }
});


router.get('/documents/excel', async (req, res) => {
    try {
        // Fetch documents from MongoDB where is_Won is true
        const documents = await Document.find({ is_Won: true });

        if (documents.length === 0) {
            return res.status(404).json({ message: 'No documents found with is_Won set to true.' });
        }

        // Create a new Excel workbook and worksheet
        const workbook = new ExcelJS.Workbook();
        const worksheet = workbook.addWorksheet('Documents');

        // Define the headers for the worksheet
        worksheet.columns = [
            { header: 'First Name', key: 'first_name', width: 20 },
            { header: 'Last Name', key: 'last_name', width: 20 },
            { header: 'Email', key: 'email', width: 30 },
            { header: 'Student ID', key: 'student_id', width: 15 },
            { header: 'Phone Number', key: 'phone_number', width: 20 },
            { header: 'Study Department', key: 'Study_Department', width: 25 },
            { header: 'Car Type', key: 'car_type', width: 20 },
            { header: 'Car Number', key: 'car_number', width: 15 },
            { header: 'License Image', key: 'licenseImage', width: 30 },
        ];

        // Add rows to the worksheet
        documents.forEach((doc) => {
            worksheet.addRow({
                first_name: doc.first_name,
                last_name: doc.last_name,
                email: doc.email,
                student_id: doc.student_id,
                phone_number: doc.phone_number,
                Study_Department: doc.Study_Department,
                car_type: doc.car_type,
                car_number: doc.car_number,
                licenseImage: doc.licenseImage,
            });
        });

        // Set the response headers for Excel file download
        res.setHeader(
            'Content-Type',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        );
        res.setHeader(
            'Content-Disposition',
            'attachment; filename="users_with_won_status.xlsx"'
        );
        await workbook.xlsx.write(res);
        res.end();
    } catch (error) {
        console.error('Error exporting users:', error);
        res.status(500).send({ error: 'Failed to export users' });
    }
});


// Route to fetch a document by student ID
router.get('/documents/:student_id', async (req, res) => {
    try {
        const { student_id } = req.params;
        const updatedDocument = await Document.findOne({ student_id });

        if (!updatedDocument) {
            return res.status(404).json({ message: 'No document found for this student.' });
        }

        res.status(200).json(updatedDocument);
    } catch (err) {
        console.error("Error fetching document:", err);
        res.status(400).json({ message: 'Error fetching document', error: err });
    }
});


// Route to fetch all documents
router.get('/documents', async (req, res) => {
    try {
        const documents = await Document.find();
        res.status(200).json(documents);
    } catch (err) {
        console.error("Error fetching documents:", err);
        res.status(400).json({ message: 'Error fetching documents', error: err });
    }
});

router.use((req, res, next) => {
    console.log(`Incoming request: ${req.method} ${req.originalUrl}`);
    next();
});




router.put('/documents/update-winners', async (req, res) => {
    try {
        const { winners } = req.body;

        if (!winners || !Array.isArray(winners) || winners.length === 0) {
            return res.status(400).json({ message: 'Invalid or empty winners list.' });
        }
        console.log('Winners list:', winners);
        
        // המתן עד שהעדכון יושלם
        const result = await Document.updateMany(
            { student_id: { $in: winners } },
            { $set: { is_won: true } }
        );

        console.log('Update result:', result);

        // שלח תשובה אחרי שהשינוי בוצע
        res.status(200).json({
            message: 'Winners updated successfully.',
            updatedCount: result.modifiedCount, // מספר המסמכים שהשתנו
        });
    } catch (err) {
        console.error('Error updating winners:', err);
        res.status(500).json({ message: 'Error updating winners.', error: err });
    }
});




// Route to update a document by student ID
router.put('/documents/:student_id', async (req, res) => {
    try {
        const { student_id } = req.params;
        const updatedData = req.body;

        if (
            !updatedData.first_name ||
            !updatedData.last_name ||
            !updatedData.email ||
            !updatedData.phone_number ||
            !updatedData.Study_Department ||
            !updatedData.car_type ||
            !updatedData.car_number ||
            !updatedData.license_image
        ) {
            return res.status(400).json({ message: 'All fields are required.' });
        }

        // Check if the student is a winner and update the is_Won field accordingly
        const isWinner = updatedData.is_Won !== undefined ? updatedData.is_Won : false;

        const updatedDocument = await Document.findOneAndUpdate(
            { student_id },
            { 
                $set: { 
                    ...updatedData,
                    is_Won: isWinner // Update the is_Won field based on the provided data
                } 
            },
            { new: true, runValidators: true }
        );

        if (!updatedDocument) {
            return res.status(404).json({ message: 'Document not found' });
        }

        res.status(200).json(updatedDocument);
    } catch (err) {
        res.status(400).json({ message: 'Error updating document', error: err });
    }
});




module.exports = router;
